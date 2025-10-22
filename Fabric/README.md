# Fabric + ADF Infrastructure as Code

This repository automates deployment of:
- Azure Data Factory
- Microsoft Fabric Capacity
- Microsoft Fabric Workspaces
- Storage Account
- Resource Groups

Each environment (dev/test/uat/prod) uses separate parameter files and variable groups linked to Azure Key Vaults.

## Structure
```
infra/
  main.bicep
  parameters-dev.json
  parameters-test.json
  parameters-uat.json
  parameters-prod.json
azure-pipelines/
  deploy-infra.yml
```

## Usage
1. Create variable groups: vg-fabric-dev/test/uat/prod linked to appropriate Key Vaults.
2. Set up service connection: `sc-azure-fabric`
3. Commit to main branch → pipeline runs automatically.