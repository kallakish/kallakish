# Fabric CI/CD Starter (Azure DevOps + `fabric-cicd`)

This starter shows how to deploy **Microsoft Fabric** items from a Git-connected workspace to another workspace using the [`fabric-cicd`](https://microsoft.github.io/fabric-cicd/0.1.30/) Python library.

## What you get
- `azure-pipelines.yml` — Azure DevOps pipeline that installs Python, installs `fabric-cicd`, and runs the deploy script using a Service Connection.
- `.deploy/fabric_workspace.py` — Python script that calls `deploy_with_config`.
- `config.yml` — Single config driving deployment per environment (dev/test/prod).
- `parameter.yml` — Example **connection & ID mapping** (e.g., Data Pipeline connections, Lakehouse/Workspace IDs, schedule toggles).
- `.env.example` — Variables you should set as DevOps secret variables (or variable group / KeyVault).
- `README.md` — You are here.

## How it works (high level)
1. **Dev workspace** is Git-connected. When you commit to the repo, Azure DevOps triggers the pipeline.
2. The pipeline runs `fabric-cicd` to **publish** the items (full publish each time) to the **target workspace** for the selected environment.
3. **Parameterization** in `parameter.yml` updates environment-specific values (e.g., connection GUIDs inside pipelines, Lakehouse IDs in notebooks).

> NOTE: `fabric-cicd` deploys only item types with source control and public create/update APIs. See docs for the latest supported item types.

## Quick start
1. Put this folder at the **root of your Fabric Git repo** (same level as your item folders).
2. In Azure DevOps create/confirm a Service Connection that can access Microsoft Fabric (recommended: Azure Resource Manager / Service Principal with Graph permissions for Fabric, or use AzureCLI with SPN).
3. In your pipeline variables (or Variable Group), set:
   - `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` (SPN)
   - `ENVIRONMENT` (e.g., `dev`, `test`, `prod`)
   - `WORKSPACE_ID_DEV|TEST|PROD` (target Fabric workspace IDs)
4. Commit and run the pipeline.

## FAQ
**Q: Will this deploy *Data Pipelines* between workspaces?**  
**A:** Yes — DataPipeline is supported. To **remap connections** per environment, use the example JSONPath rule in `parameter.yml`.

**Q: How do connections change dynamically?**  
**A:** Use `key_value_replace` (JSONPath) and `find_replace` in `parameter.yml` to swap connection GUIDs, Lakehouse IDs, gateway bindings etc. The library performs the replacements before publishing.

**Q: Can I select only a few items to deploy?**  
**A:** Full deploys are recommended. Selective deploy is possible via `config.yml` feature flags but use with caution.

---

MIT-licensed. Generated starter.
