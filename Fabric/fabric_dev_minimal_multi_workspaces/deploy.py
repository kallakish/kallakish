import argparse
import os
from fabric_cicd import FabricWorkspace, publish_all_items

def main(workspace_id, environment, repo_dir, item_types):
    client_id = os.environ["FABRIC_CLIENT_ID"]
    tenant_id = os.environ["FABRIC_TENANT_ID"]
    client_secret = os.environ["FABRIC_CLIENT_SECRET"]

    ws = FabricWorkspace(
        workspace_id=workspace_id,
        environment=environment,
        repository_directory=repo_dir,
        item_type_in_scope=item_types,
        client_id=client_id,
        tenant_id=tenant_id,
        client_secret=client_secret
    )
    publish_all_items(ws)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy to Microsoft Fabric workspace using fabric-cicd.")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--repo-dir", required=True, help="Path to the workspace's fabric_items directory")
    parser.add_argument("--item-types", nargs="+", default=["Notebook", "DataPipeline", "Environment"])
    args = parser.parse_args()
    main(args.workspace_id, args.environment, args.repo_dir, args.item_types)