import json
import sys
from pathlib import Path

IR_TYPE = "microsoft.datafactory/factories/integrationruntimes"

def is_ir(res: dict) -> bool:
    t = (res or {}).get("type", "")
    return isinstance(t, str) and t.lower() == IR_TYPE

def patch_resource(res):
    """Remove dependsOn references to integrationRuntimes; recurse nested resources."""
    if isinstance(res, dict):
        dep = res.get("dependsOn")
        if isinstance(dep, list):
            res["dependsOn"] = [
                d for d in dep
                if isinstance(d, str) and "integrationruntimes" not in d.lower()
            ]

        nested = res.get("resources")
        if isinstance(nested, list):
            res["resources"] = [patch_resource(r) for r in nested if not is_ir(r)]

    return res

def main():
    if len(sys.argv) != 3:
        print("Usage: remove_ir_from_arm.py <inTemplate.json> <outTemplate.json>", file=sys.stderr)
        return 2

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    with in_path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    resources = doc.get("resources", [])
    if isinstance(resources, list):
        before = len(resources)
        resources = [patch_resource(r) for r in resources if not is_ir(r)]
        after = len(resources)
        doc["resources"] = resources
        print(f"Removed {before - after} integration runtime resource(s).")
    else:
        print("WARNING: No top-level 'resources' list found; nothing chang
