#!/usr/bin/env python3
"""
Generate parameter.yml for a Fabric workspace repo folder (Git-integration or classic).
This version coerces all values into YAML-safe types to avoid RepresenterError.

Usage:
  python generate_parameter_template.py \
      --workspace-id <DEV-WORKSPACE-GUID> \
      --workspace-root <path-to-workspace-folder> \
      --output parameter.yml
"""
import argparse, json, os, re
from pathlib import Path
from collections import defaultdict
from typing import Any

try:
    import yaml
except Exception:
    raise SystemExit("PyYAML is required: pip install pyyaml")

GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")

ID_KEYS = {
    "lakehouseId","warehouseId","kqlDatabaseId",
    "semanticModelId","modelId","datasetId",
    "workspaceId","connectionId","sourceId"
}
CONNECTION_PUBLIC = {"server","database","url","endpoint","account","container","fileSystem","scope","resourceId"}
CONNECTION_SECRET = {"password","sas","sasToken","secret","clientSecret","sharedKey","connectionString"}

def infer_item_type(path: Path) -> str | None:
    s = str(path)
    if ".DataPipeline" in s: return "DataPipeline"
    if ".Notebook"     in s: return "Notebook"
    if ".Lakehouse"    in s: return "Lakehouse"
    if ".SemanticModel"in s: return "SemanticModel"
    if ".Report"       in s: return "Report"
    if ".Warehouse"    in s: return "Warehouse"
    if ".Connection"   in s: return "Connection"
    return None

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def collect_from_json(obj, item_type: str, refs, conn_fields):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ID_KEYS and isinstance(v, str) and GUID_RE.fullmatch(v or ""):
                refs[(k, v, item_type or "Notebook")] += 1
            if k == "connectionDetails" and isinstance(v, dict):
                for ck, cv in v.items():
                    if isinstance(cv, str) and cv:
                        if ck in CONNECTION_PUBLIC: conn_fields[("public", ck, cv)] += 1
                        if ck in CONNECTION_SECRET: conn_fields[("secret", ck, cv)] += 1
            collect_from_json(v, item_type, refs, conn_fields)
    elif isinstance(obj, list):
        for it in obj:
            collect_from_json(it, item_type, refs, conn_fields)

def collect_from_text(text: str, item_type: str, refs):
    for m in GUID_RE.finditer(text or ""):
        refs[("unknown", m.group(0), item_type or "Notebook")] += 1

def scan_workspace(root: Path):
    refs = defaultdict(int)
    conn_fields = defaultdict(int)

    candidates = []
    if (root / "items").is_dir(): candidates.append(root / "items")
    candidates.append(root)

    seen = set()
    for base in candidates:
        for p in base.rglob("*"):
            if not p.is_file(): continue
            if p in seen: continue
            seen.add(p)

            item_type = infer_item_type(p)

            if p.name in ("pipeline-content.json","definition.json") or p.suffix.lower()==".ipynb":
                obj = load_json(p)
                if obj is not None:
                    collect_from_json(obj, item_type, refs, conn_fields)
                    continue

            if p.suffix.lower()==".py" and (".Notebook" in str(p.parent) or p.name=="notebook-content.py"):
                try:
                    collect_from_text(p.read_text(encoding="utf-8", errors="ignore"), item_type, refs)
                except Exception:
                    pass

    return refs, conn_fields

def yamlify(obj: Any) -> Any:
    """Coerce to YAML-friendly primitives: dict/list/str/int/float/bool/None."""
    from collections import OrderedDict, defaultdict
    if isinstance(obj, (str,int,float,bool)) or obj is None:
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (list, tuple, set)):
        return [yamlify(x) for x in obj]
    if isinstance(obj, (dict, OrderedDict, defaultdict)):
        # YAML requires string keys; coerce everything to str keys
        return {str(k): yamlify(v) for k, v in obj.items()}
    # fallback to string
    return str(obj)

def build_parameter_yaml(dev_ws_id: str, refs, conn_fields):
    fr: list[dict] = []

    # Map workspace id -> $workspace.$id
    for t in ["Notebook","DataPipeline","SemanticModel","Report"]:
        fr.append({
            "find_value": dev_ws_id,
            "replace_value": {"DEV":"$workspace.$id","TEST":"$workspace.$id","PROD":"$workspace.$id"},
            "item_type": t
        })

    # Other GUIDs
    for (k, guid, item_type), _cnt in sorted(refs.items(), key=lambda x: (x[0][2], x[0][0] or "", x[0][1])):
        if k == "workspaceId":
            continue
        fr.append({
            "find_value": guid,
            "replace_value": {
                "DEV":  guid,
                "TEST": f"TODO-REPLACE-{(k or 'ID').upper()}-TEST",
                "PROD": f"TODO-REPLACE-{(k or 'ID').upper()}-PROD",
            },
            "item_type": item_type or "Notebook",
        })

    # Connection fields
    for (kind, field, value), _cnt in sorted(conn_fields.items()):
        if not value: continue
        if kind == "public":
            replace = {
                "DEV":  value,
                "TEST": f"TODO-REPLACE-{field.upper()}-TEST",
                "PROD": f"TODO-REPLACE-{field.upper()}-PROD",
            }
        else:  # secret
            var = field.upper()
            replace = {
                "DEV":  f"$env:{var}_DEV",
                "TEST": f"$env:{var}_TEST",
                "PROD": f"$env:{var}_PROD",
            }
        fr.append({
            "find_value": value,
            "replace_value": replace,
            "item_type": "Connection",
        })

    return {"find_replace": fr}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-id", required=True)
    ap.add_argument("--workspace-root", required=True)
    ap.add_argument("--output", default="parameter.yml")
    args = ap.parse_args()

    dev_ws_id = re.sub(r"[^0-9a-fA-F-]", "", args.workspace_id)
    if not GUID_RE.fullmatch(dev_ws_id):
        raise SystemExit(f"Invalid workspace GUID: {args.workspace_id}")

    root = Path(args.workspace_root).resolve()
    if not root.exists():
        raise SystemExit(f"workspace-root not found: {root}")

    refs, conn_fields = scan_workspace(root)
    param = build_parameter_yaml(dev_ws_id, refs, conn_fields)

    # Coerce everything before dump (prevents RepresenterError)
    yaml_ready = yamlify(param)

    out = Path(args.output)
    if not out.is_absolute(): out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)

    # Optional: validate each entry to catch the exact offender (debug aid)
    for i, entry in enumerate(yaml_ready.get("find_replace", []), 1):
        try:
            yaml.safe_dump(entry)
        except Exception as e:
            print(f"[ERROR] YAML cannot represent find_replace entry #{i}: {entry}\n{e}")
            raise

    with out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(yaml_ready, fh, sort_keys=False, allow_unicode=True)

    print(f"[OK] parameter.yml written: {out}")
    print(f"##vso[task.setvariable variable=fabric_parameter_file]{out}")

if __name__ == "__main__":
    main()
