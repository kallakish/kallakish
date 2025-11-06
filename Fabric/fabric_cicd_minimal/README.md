# fabric-cicd — minimal setup

Files:
- `config.yml` — workspace ids, items folder, parameter file.
- `parameter.yml` — optional per-environment replacements.
- `.deploy/fabric_workspace.py` — tiny runner that calls deploy_with_config.

Azure DevOps example:

```yaml
- task: AzureCLI@2
  displayName: 'Deploy (minimal)'
  inputs:
    azureSubscription: 'your-service-connection'
    scriptType: ps
    scriptLocation: inlineScript
    inlineScript: |
      $py = "C:\Program Files\Python312\python.exe"
      if (-not (Test-Path $py)) { $py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" }
      & $py -m pip install -U pip
      & $py -m pip install fabric-cicd==0.1.30 azure-identity
      & $py -u .\.deployabric_workspace.py --environment $(ENVIRONMENT)
```
