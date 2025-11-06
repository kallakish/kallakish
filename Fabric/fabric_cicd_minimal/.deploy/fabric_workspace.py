#!/usr/bin/env python3
# Minimal runner: deploy using config.yml
import os, argparse
from pathlib import Path
from fabric_cicd import deploy_with_config
from azure.identity import DefaultAzureCredential, ClientSecretCredential

def _cred():
    tid, cid, sec = os.getenv("TENANT_ID"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")
    if tid and cid and sec:
        return ClientSecretCredential(tid, cid, sec)
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)

def main():
    ap = argparse.ArgumentParser(description="fabric-cicd minimal deploy")
    ap.add_argument("--environment", required=True, help="Environment key in config.yml (e.g., dev|test|prod)")
    args = ap.parse_args()

    cfg = Path(__file__).resolve().parent.parent / "config.yml"
    if not cfg.exists():
        raise FileNotFoundError(f"config.yml not found at {cfg}")
    deploy_with_config(str(cfg), environment=args.environment, token_credential=_cred())

if __name__ == "__main__":
    main()
