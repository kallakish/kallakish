#!/usr/bin/env python3
"""
Generate a Fabric parameter.yml from a DEV workspace export.

It walks the repo's workspace folder (the one that contains 'items/'), looks for:
  - common GUID references like lakehouseId/modelId/warehouseId/kqlDatabaseId/datasetId/workspaceId
  - connection definitions (server/database/url/account/etc.)
and produces a parameter.yml with DEV values pre-filled and TEST/PROD placeholders.

Usage:
  python generate_parameter_template.py \
      --workspace-id <DEV_WORKSPACE_GUID> \
      --workspace-root workspaces/workspace_alpha \   # folder that contains 'fabric_items' or 'items'
      --output parameter.yml \
      --env DEV

Env (optional): none required. No API calls are made; this script only scans the repo.

Exit codes:
  0 success
  10 bad args or missing folder
"""

import argparse
import json
import os
import re
from pathlib import Path
from collections import defaultdict, OrderedDict

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml", flush=True)
    raise

GUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")

# Keys we consider "ID references" inside items (not the item's own ID)
ID_KEYS = {
    "lakehouseId": ["Notebook", "DataPipeline"],
    "warehouseId": ["Notebook", "DataPipeline"],
    "kqlDatabaseId": ["Notebook", "DataPipeline"],
    "semanticModelId": ["Report", "SemanticModel"],
    "modelId": ["Report", "SemanticModel"],
    "datasetId": ["Report", "SemanticModel"],
    "workspaceId": ["Notebook", "DataPipeline", "SemanticModel", "Report"],  # will be mapped to $workspace.$id
    "connectionId": ["Notebook", "DataPipeline", "SemanticModel"],
    "sourceId": ["DataPipeline"],
}

# Connection detail fields to parameterize (non-secret)
CONNECTION_PUBLIC_FIELDS = {
    "server",
    "database",
    "url",
    "account",
    "endpoint",
    "container",
    "fileSystem",
    "scope",
    "tenantId",
    "clientId",
    "resourceId",
}

# Connection secret-ish fields — we map to $env:<VAR> instead of writing dev values
CONNECTION_SECRET_FIELDS = {
    "password",
    "sas",
    "sasToken",
    "secret",
    "clientSecret",
    "sharedKey",
    "connectionString",
}

def is_guid(val: str) -> bool:
    return isinstance(val, str) and bool(GUID_RE.match(val))

def infer_item_type_from_path(p: Path) -> str | None:
    """
    Tries to infer the item_type to target for replacements
    by looking at the folder name suffix (e.g., 'Hello Notebook.Notebook').
    """
    # Traverse up to the direct item folder .../<Some Name>.<Type>/
    for parent in [p] + list(p.parents):
        name = parent.name
        if "." in name:
            suffix = name.split(".")[-1].strip()
            # normalize a few common ones
            mapping = {
                "Notebook": "Notebook",
                "Data": None,  # 'Data Pipeline' comes as two tokens sometimes
                "Pipeline": "DataPipeline",
                "DataPipeline": "DataPipeline",
                "Lakehouse": "Lakehouse",
                "SemanticModel": "SemanticModel",
                "Report": "Report",
                "Warehouse": "Warehouse",
                "KQLDatabase": "KQLDatabase",
                "Connection": "Connection",
                "Environment": "Environment",
            }
            if suffix in mapping and mapping[suffix]:
                return mapping[suffix]
            # handle 'Data Pipeline' as folder with space
            if name.endswith("Data Pipeline"):
                return "DataPipeline"
    return None

def walk_json_like_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in [".json", ".ipynb"]:  # notebooks are JSON too
            # Skip very large files if needed; here we try anyway
            try:
                text = p.read_text(encoding="utf-8")
                yield p, json.loads(text)
            except Exception:
                # not valid JSON; ignore
                continue

def deep_collect_refs(obj, path_stack, current_item_type, refs, conn_fields):
    """
    Walk arbitrary JSON, collecting interesting GUIDs keyed by their JSON key,
    and connection detail fields for parameterization.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            path_stack.append(k)
            # Collect ID references
            if k in ID_KEYS and isinstance(v, str) and is_guid(v):
                hinted_types = ID_KEYS[k]
                # prefer the item type we're currently in, else include all hinted
                target_types = [current_item_type] if current_item_type in hinted_types else hinted_types
                for t in target_types:
                    refs[(k, v, t)] += 1

            # Collect connection details
            if "connectionDetails" in path_stack or (current_item_type == "Connection"):
                if isinstance(v, str):
                    key_lower = k  # keep original key
                    if k in CONNECTION_PUBLIC_FIELDS and v:
                        conn_fields[("public", k, v)] += 1
                    if k in CONNECTION_SECRET_FIELDS and v:
                        conn_fields[("secret", k, v)] += 1

            deep_collect_refs(v, path_stack, current_item_type, refs, conn_fields)
            path_stack.pop()
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path_stack.append(str(i))
            deep_collect_refs(v, path_stack, current_item_type, refs, conn_fields)
            path_stack.pop()
    else:
        # primitives — nothing to do
        return

def generate_parameter_yaml(dev_workspace_id: str, workspace_root: Path) -> dict:
    """
    Build the parameter.yml structure as a Python dict.
    """
    # Find the actual items root: either <root>/items or <root>/fabric_items/items
    candidates = [workspace_root / "items", workspace_root / "fabric_items" / "items"]
    items_root = None
    for c in candidates:
        if c.exists() and c.is_dir():
            items_root = c
            break
    if not items_root:
        raise FileNotFoundError(f"Couldn't locate an 'items/' folder under {workspace_root}")

    refs = defaultdict(int)        # key: (json_key, guid_value, item_type)
    conn_fields = defaultdict(int) # key: ("public"/"secret", field_name, value)

    for p, data in walk_json_like_files(items_root):
        item_type = infer_item_type_from_path(p)
        deep_collect_refs(data, [], item_type, refs, conn_fields)

    # Start assembling the YAML structure
    param = OrderedDict()
    param["find_replace"] = []

    # WorkspaceId → $workspace.$id (so we never hardcode dev workspace id)
    # Apply to common types that embed workspaceId
    for t in ["Notebook", "DataPipeline", "SemanticModel", "Report"]:
        param["find_replace"].append(OrderedDict([
            ("find_value", dev_workspace_id),
            ("replace_value", OrderedDict([
                ("DEV", "$workspace.$id"),
                ("TEST", "$workspace.$id"),
                ("PROD", "$workspace.$id"),
            ])),
            ("item_type", t),
        ]))

    # Other GUID references we discovered
    for (json_key, guid_val, item_type), _count in sorted(refs.items()):
        # Skip workspaceId here; we already handled it with the dynamic mapping above
        if json_key == "workspaceId":
            continue
        # Build a friendly comment-like description via a dict key
        entry = OrderedDict()
        entry["find_value"] = guid_val
        entry["replace_value"] = OrderedDict([
            ("DEV", guid_val),
            ("TEST", "TODO-REPLACE-WITH-TEST-" + json_key.upper()),
            ("PROD", "TODO-REPLACE-WITH-PROD-" + json_key.upper()),
        ])
        if item_type:
            entry["item_type"] = item_type
        else:
            # Fall back to applying broadly if we couldn't infer
            entry["item_type"] = "Notebook"
        param["find_replace"].append(entry)

    # Connection details — inject env vars for secrets; keep public values as per-env maps
    # We'll target item_type "Connection"
    # Public fields: keep DEV value; set TEST/PROD placeholders to fill
    for (kind, field, value), _cnt in sorted(conn_fields.items()):
        entry = OrderedDict()
        entry["find_value"] = value
        if kind == "public":
            entry["replace_value"] = OrderedDict([
                ("DEV", value),
                ("TEST", f"TODO-REPLACE-{field.upper()}-TEST"),
                ("PROD", f"TODO-REPLACE-{field.upper()}-PROD"),
            ])
        else:  # secret
            # map to environment variables so secrets aren't committed
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
    ap.add_argument("--workspace-id", required=True, help="DEV workspace GUID (used to map to $workspace.$id)")
    ap.add_argument("--workspace-root", required=True, help="Path to the workspace folder that contains 'items/'")
    ap.add_argument("--output", default="parameter.yml", help="Output YAML file path (default: parameter.yml in root)")
    ap.add_argument("--env", default="DEV", help="Name of the dev environment label (default: DEV)")
    args = ap.parse_args()

    root = Path(args.workspace_root).resolve()
    if not root.exists():
        print(f"[ERROR] workspace-root not found: {root}", flush=True)
        raise SystemExit(10)

    dev_ws_id = "".join(ch for ch in args.workspace_id if ch in "0123456789abcdefABCDEF-")
    if not GUID_RE.match(dev_ws_id):
        print(f"[ERROR] workspace-id is not a valid GUID: {args.workspace_id}", flush=True)
        raise SystemExit(10)

    param = generate_parameter_yaml(dev_ws_id, root)

    out = Path(args.output)
    if not out.is_absolute():
        out = root / out

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(param, fh, sort_keys=False, allow_unicode=True)

    # Print a short summary
    counts = len(param.get("find_replace", []))
    print(f"[OK] Wrote {counts} find_replace entries to: {out}")
    # Set ADO variable for downstream steps
    print(f"##vso[task.setvariable variable=fabric_parameter_file]{out}")

if __name__ == "__main__":
    main()
