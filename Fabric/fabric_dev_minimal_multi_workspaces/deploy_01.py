#!/usr/bin/env python3
"""
Deploy Fabric workspace content using fabric-cicd.

Args:
  --workspace-id      GUID of the target workspace (use the cleaned id from preflight)
  --environment       ENV key used by parameter.yml (e.g., DEV / TEST / PROD)
  --repo-dir          Path to the workspace's 'items' root (Git export)
  --items-in-scope    Comma list of item types (default: all common types)
  --no-unpublish      Skip unpublishing orphan items (default: unpublish)
Env:
  AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_CLIENT_SECRET (used by azure-identity)
  SYSTEM_DEBUG=true for verbose logs
Exit codes:
  0 = success
  10 = invalid args/path
  11 = deploy error
"""

import os, sys, argparse
from pathlib import Path

def main():
    try:
        from fabric_cicd import (
            FabricWorkspace,
            publish_all_items,
            unpublish_all_orphan_items,
            change_log_level,
        )
    except Exception as e:
        print(f"[ERROR] fabric-cicd not installed: {e}", flush=True)
        sys.exit(11)

    if os.getenv("SYSTEM_DEBUG", "false").lower() == "true":
        change_log_level("DEBUG")

    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-id", required=True)
    ap.add_argument("--environment", required=True)
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--items-in-scope",
                    default="Notebook,DataPipeline,Environment,Lakehouse,SemanticModel,Report")
    ap.add_argument("--no-unpublish", action="store_true")
    args = ap.parse_args()

    repo_dir = Path(args.repo_dir).resolve()
    if not repo_dir.exists():
        print(f"[ERROR] repo-dir not found: {repo_dir}", flush=True)
        sys.exit(10)

    items = [x.strip() for x in args.items_in_scope.split(",") if x.strip()]
    print(f"WorkspaceId: {args.workspace_id}")
    print(f"Environment: {args.environment}")
    print(f"Repository:  {repo_dir}")
    print(f"Items:       {', '.join(items)}")

    # fabric-cicd uses DefaultAzureCredential under the hood; with AZURE_* envs set,
    # it will authenticate as your SPN (same identity as the preflight).
    try:
        ws = FabricWorkspace(
            workspace_id=args.workspace_id,
            environment=args.environment,
            repository_directory=str(repo_dir),
            item_type_in_scope=items,
        )
        publish_all_items(ws)
        if not args.no_unpublish:
            unpublish_all_orphan_items(ws)
        print("[OK] Deployment completed.", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}", flush=True)
        sys.exit(11)

if __name__ == "__main__":
    main()
