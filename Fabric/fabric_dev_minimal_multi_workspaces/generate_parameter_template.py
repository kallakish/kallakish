#!/usr/bin/env python3
"""
Generate parameter.yml for a Fabric workspace repo folder.

Works with both layouts:
  A) Classic: <root>/items/**/*
  B) Git-integration: <root>/{Pipelines,Notebooks,Reports,Lakehouses,...}/**/*

Finds GUID references in JSON files (pipeline-content.json, definition.json, *.ipynb)
and best-effort in notebook-content.py (regex). Produces parameter.yml where:
  - workspaceId is mapped to $workspace.$id
  - other ids keep DEV value and add TEST/PROD placeholders
  - connection secrets map to $env:* placeholders (you supply via pipeline env vars)

Usage:
  python generate_parameter_template.py \
      --workspace-id <DEV-WORKSPACE-GUID> \
      --workspace-root <path-to-workspace-folder> \
      --output parameter.yml
"""

import argparse, json, os, re
from pathlib import Path
from collections import defaultdict, OrderedDict

try:
    import yaml
except Exception:
    raise SystemExit("PyYAML is required: pip install pyyaml")

GUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")

# JSON keys we treat as "external id references"
ID_KEYS = {
    "lakehouseId", "warehouseId", "kqlDatabaseId",
    "semanticModelId", "modelId", "datasetId",
    "workspaceId", "connectionId", "sourceId"
}

# Connection fields
CONNECTION_PUBLIC = {"server","database","url","endpoint","account","container","fileSystem","scope","resourceId"}
CONNECTION_SECRET = {"password","sas","sasToken","secret","clientSecret","sharedKey","connectionString"}

def infer_item_type(path: Path) -> str | None:
    n = path.name
    # prefer the folder that ends with .<Type>
    for parent in [path] + list(path.parents):
        name = parent.name
        if name.endswith(".DataPipeline"): return "DataPipeline"
        if name.endswith(".Notebook"):     return "Notebook"
        if name.endswith(".Lakehouse"):    return "Lakehouse"
        if name.endswith(".SemanticModel"):return "SemanticModel"
        if name.endswith(".Report"):       return "Report"
        if name.endswith(".Warehouse"):    return "Warehouse"
        if name.endswith(".Connection"):   return "Connection"
    return None

def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def collect_from_json(obj, item_type: str, refs, conn_fields):
    if isinstance(obj, dict):
        for k, v in obj.items():
            # IDs
            if k in ID_KEYS and isinstance(v, str) and GUID_RE.fullmatch(v or ""):
                refs[(k, v, item_type)] += 1
            # connection details block
            if k == "connectionDetails" and isinstance(v, dict):
                for ck, cv in v.items():
                    if isinstance(cv, str) and cv:
                        if ck in CONNECTION_PUBLIC:
                            conn_fields[("public", ck, cv)] += 1
                        if ck in CONNECTION_SECRET:
                            conn_fields[("secret", ck, cv)] += 1
            # recurse
            collect_from_json(v, item_type, refs, conn_fields)
    elif isinstance(obj, list):
        for it in obj:
            collect_from_json(it, item_type, refs, conn_fields)

def collect_from_text(text: str, item_type: str, refs):
    # best-effort: capture raw GUIDs inside .py notebooks
    for m in GUID_RE.finditer(text or ""):
        refs[("unknown", m.group(0), item_type or "Notebook")] += 1

def scan_workspace(root: Path):
    """
    Returns (refs, conn_fields)
    refs: map (json_key, guid, item_type) -> count
    conn_fields: map (kind, field, value) -> count
    """
    refs = defaultdict(int)
    conn_fields = defaultdict(int)

    candidates = []
    # A) 'items' layout
    if (root / "items").is_dir():
        candidates.append(root / "items")
    # B) Git integration layout (scan all)
    candidates.append(root)

    seen = set()
    for base in candidates:
        for p in base.rglob("*"):
            if not p.is_file(): continue
            if p in seen: continue
            seen.add(p)

            item_type = infer_item_type(p)

            # JSON-bearing files we care about
            if p.name in ("pipeline-content.json","definition.json") or p.suffix.lower()==".ipynb":
                obj = load_json(p)
                if obj is not None:
                    collect_from_json(obj, item_type, refs, conn_fields)
                    continue

            # best-effort for notebook-content.py or any .py inside a .Notebook folder
            if p.suffix.lower()==".py" and (".Notebook" in str(p.parent) or p.name=="notebook-content.py"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    collect_from_text(text, item_type, refs)
                except Exception:
                    pass

    return refs, conn_fields

def build_parameter_yaml(dev_ws_id: str, refs, conn_fields):
    param = OrderedDict()
    param["find_replace"] = []

    # Always map workspace id to $workspace.$id (for common types)
    for t in ["Notebook","DataPipeline","SemanticModel","Report"]:
        entry = OrderedDict()
        entry["find_value"] = dev_ws_id
        entry["replace_value"] = OrderedDict([("DEV","$workspace.$id"),("TEST","$workspace.$id"),("PROD","$workspace.$id")])
        entry["item_type"] = t
        param["find_replace"].append(entry)

    # Other GUIDs
    for (k, guid, item_type), _cnt in sorted(refs.items(), key=lambda x: (x[0][2] or "", x[0][0] or "", x[0][1])):
        if k == "workspaceId":  # already handled
            continue
        entry = OrderedDict()
        entry["find_value"] = guid
        entry["replace_value"] = OrderedDict([
            ("DEV", guid),
            ("TEST", f"TODO-REPLACE-{(k or 'ID').upper()}-TEST"),
            ("PROD", f"TODO-REPLACE-{(k or 'ID').upper()}-PROD"),
        ])
        entry["item_type"] = item_type or "Notebook"
        param["find_replace"].append(entry)

    # Connection fields
    for (kind, field, value), _cnt in sorted(conn_fields.items()):
        entry = OrderedDict()
        entry["find_value"] = value
        if kind == "public":
            entry["replace_value"] = OrderedDict([
                ("DEV", value),
                ("TEST", f"TODO-REPLACE-{field.upper()}-TEST"),
                ("PROD", f"TODO-REPLACE-{field.upper()}-PROD"),
            ])
        else:
            # secrets pull from env at deploy time
            var = field.upper()
            entry["replace_value"] = OrderedDict([
                ("DEV", f"$env:{var}_DEV"),
                ("TEST", f"$env:{var}_TEST"),
                ("PROD", f"$env:{var}_PROD"),
            ])
        entry["item_type"] = "Connection"
        param["find_replace"].append(entry)

    return param

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-id", required=True, help="DEV workspace GUID")
    ap.add_argument("--workspace-root", required=True, help="Folder that contains Pipelines/, Notebooks/, etc. (or items/)")
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

    out = Path(args.output)
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(param, fh, sort_keys=False, allow_unicode=True)

    print(f"[OK] parameter.yml written: {out}")
    print(f"##vso[task.setvariable variable=fabric_parameter_file]{out}")

if __name__ == "__main__":
    main()
