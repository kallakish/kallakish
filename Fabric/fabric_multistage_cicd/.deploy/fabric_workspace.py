#!/usr/bin/env python
import argparse
import os
from pathlib import Path
from fabric_cicd import deploy_with_config
from azure.identity import ClientSecretCredential, DefaultAzureCredential

def main():
    parser = argparse.ArgumentParser(description="Deploy Fabric items using fabric-cicd + config.yml (multi-stage)")
    parser.add_argument("--environment", required=True, help="Environment key in config.yml (dev|test|prod)")
    parser.add_argument("--workspace_id_dev", default="", help="Override dev workspace ID")
    parser.add_argument("--workspace_id_test", default="", help="Override test workspace ID")
    parser.add_argument("--workspace_id_prod", default="", help="Override prod workspace ID")
    args = parser.parse_args()

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    if tenant_id and client_id and client_secret:
        credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    else:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

    override_ws = {}
    if args.workspace_id_dev:
        override_ws["dev"] = args.workspace_id_dev
    if args.workspace_id_test:
        override_ws["test"] = args.workspace_id_test
    if args.workspace_id_prod:
        override_ws["prod"] = args.workspace_id_prod

    config_override = {"core": {"workspace_id": override_ws}} if override_ws else None

    deploy_with_config(
        config_file_path=str(Path(__file__).parent.parent / "config.yml"),
        environment=args.environment,
        token_credential=credential,
        config_override=config_override
    )

if __name__ == "__main__":
    main()
