#!/usr/bin/env python
import argparse
import os
from pathlib import Path

# fabric-cicd imports
from fabric_cicd import deploy_with_config
from azure.identity import ClientSecretCredential, DefaultAzureCredential

def main():
    parser = argparse.ArgumentParser(description="Deploy Fabric items using fabric-cicd + config.yml")
    parser.add_argument("--environment", required=True, help="Environment key in config.yml (e.g., dev|test|prod)")
    parser.add_argument("--workspace_id_dev", required=False, default="", help="Workspace ID for dev (optional, will override config.yml if provided)")
    parser.add_argument("--workspace_id_test", required=False, default="", help="Workspace ID for test (optional)")
    parser.add_argument("--workspace_id_prod", required=False, default="", help="Workspace ID for prod (optional)")

    args = parser.parse_args()

    # Prefer explicit SPN if provided; otherwise fall back to DefaultAzureCredential (e.g., from AzureCLI@2)
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    credential = None
    if tenant_id and client_id and client_secret:
        credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    else:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

    # Optionally override workspace ids at runtime
    config_override = {}
    override_ws = {}
    if args.workspace_id_dev:
        override_ws["dev"] = args.workspace_id_dev
    if args.workspace_id_test:
        override_ws["test"] = args.workspace_id_test
    if args.workspace_id_prod:
        override_ws["prod"] = args.workspace_id_prod
    if override_ws:
        config_override = {"core": {"workspace_id": override_ws}}

    # Run deploy
    deploy_with_config(
        config_file_path=str(Path(__file__).parent.parent / "config.yml"),
        environment=args.environment,
        token_credential=credential,
        config_override=config_override or None
    )

if __name__ == "__main__":
    main()
