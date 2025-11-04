# Fabric CI/CD Starter (Azure DevOps + `fabric-cicd`)

Multi-stage pipeline (Dev → Test → Prod) with distinct **variable groups** per stage.

- `azure-pipelines.yml` — Multi-stage with separate groups (Fabric-Dev/Test/Prod) and optional manual approvals for Test/Prod.
- `.deploy/fabric_workspace.py` — Calls `deploy_with_config` from `fabric-cicd` (SPN or AzureCLI auth).
- `config.yml` — Environment mappings + flags.
- `parameter.yml` — Examples for swapping **Data Pipeline connections** (JSONPath) and **Lakehouse/Workspace IDs** (regex).
- `.env.example` — Secrets to store in variable groups or Key Vault.

**Docs:** https://microsoft.github.io/fabric-cicd/0.1.30/
