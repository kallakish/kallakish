- task: PowerShell@2
  displayName: 'Create/Ensure Fabric workspaces + RBAC (Python when exists)'
  inputs:
    targetType: 'inline'
    script: |
      $ErrorActionPreference = 'Stop'

      $fabPath     = "C:\Program Files\Python312\Scripts\fab.exe"
      $py          = "C:\Program Files\Python312\python.exe"
      $configPath  = "$(Build.SourcesDirectory)\infra\workspaces.json"

      if (-not (Test-Path $configPath)) { throw "Config file not found: $configPath" }

      # Install Py deps (for ensure_rbac.py) once
      & $py -m pip install -U pip requests azure-identity

      # list existing workspaces by name
      Write-Host "Fetching existing workspaces using 'fab ls'..."
      $lsOutput = & $fabPath ls 2>&1
      $existingNames = $lsOutput |
        Where-Object { $_ -match '\.Workspace\s*$' } |
        ForEach-Object { ($_ -split '\.Workspace')[0].Trim() }

      # helper: set multiple admins with fab.exe (for new workspaces path)
      function Ensure-Admins-Fab {
        param([string]$WorkspaceName, [string[]]$Admins)
        if (-not $Admins -or $Admins.Count -eq 0) { return }
        $Admins = $Admins | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ } | Select-Object -Unique
        foreach ($a in $Admins) {
          Write-Host "    - fab: ensuring Admin '$a' on '$WorkspaceName'..."
          & $fabPath acl set "$WorkspaceName.Workspace" -I $a -R admin -f
          if ($LASTEXITCODE -ne 0) { Write-Warning "      fab acl set failed for '$a' (exit $LASTEXITCODE) — continuing" }
        }
      }

      # load config rows
      $rows = Get-Content $configPath -Raw | ConvertFrom-Json
      $rows = @($rows)

      for ($i = 0; $i -lt $rows.Count; $i++) {
        $ws = $rows[$i]
        $name     = [string]$ws.workspaceName
        $capacity = [string]$ws.capacityName

        # admins can be adminObjectIds[] (preferred) or legacy adminObjectId
        $admins = @()
        if ($ws.PSObject.Properties.Name -contains 'adminObjectIds') {
          $admins = @($ws.adminObjectIds)
        } elseif ($ws.PSObject.Properties.Name -contains 'adminObjectId' -and $ws.adminObjectId) {
          $admins = @("$($ws.adminObjectId)")
        }

        if ([string]::IsNullOrWhiteSpace($name))     { Write-Warning "Skip index $i: no workspaceName"; continue }
        if ([string]::IsNullOrWhiteSpace($capacity)) { throw "capacityName missing at index $i for '$name'" }

        Write-Host "-------------------------------------------------"
        Write-Host "[$i] Workspace : $name"
        Write-Host "     Capacity  : $capacity"
        Write-Host "     Admins    : $($admins -join ', ')"

        if ($existingNames -contains $name) {
          Write-Host "  - Workspace exists → calling Python ensure_rbac.py (adds any missing Admins)…"
          # Use SPN creds for Python, if you’re not running under AzureCLI@2:
          $env:TENANT_ID     = "$(tenant_id)"
          $env:CLIENT_ID     = "$(dev_client_id)"
          $env:CLIENT_SECRET = "$(dev_client_secret)"
          $env:WORKSPACE_RBAC_FILE = $configPath
          $env:WORKSPACE_FILTER    = $name
          & $py -u .\.deploy\ensure_rbac.py
          if ($LASTEXITCODE -ne 0) { throw "ensure_rbac.py failed (exit $LASTEXITCODE)" }
          continue
        }

        # Create and then set admins (using fab.exe path)
        Write-Host "  - Creating workspace '$name' on capacity '$capacity'..."
        & $fabPath create "$name.Workspace" -P "capacityname=$capacity"
        if ($LASTEXITCODE -ne 0) { throw "Failed to create workspace '$name' (exit $LASTEXITCODE)" }

        Write-Host "  - Setting Admins on new workspace (fab)..."
        Ensure-Admins-Fab -WorkspaceName $name -Admins $admins

        # optional: default folders & lakehouses
        function New-FabItem { param([string]$Path,[string]$Type)
          Write-Host "    - Creating $Type '$Path.$Type'..."
          & $fabPath create "$Path.$Type"
          if ($LASTEXITCODE -ne 0) { throw "Failed to create $Type '$Path' (exit $LASTEXITCODE)." }
        }
        New-FabItem -Path "$name.Workspace/Pipelines"  -Type "Folder"
        New-FabItem -Path "$name.Workspace/Notebooks"  -Type "Folder"
        New-FabItem -Path "$name.Workspace/Scripts"    -Type "Folder"
        New-FabItem -Path "$name.Workspace/Lakehouses" -Type "Folder"
        New-FabItem -Path "$name.Workspace/Lakehouses/bronze" -Type "Lakehouse"
        New-FabItem -Path "$name.Workspace/Lakehouses/silver" -Type "Lakehouse"
        New-FabItem -Path "$name.Workspace/Lakehouses/gold"   -Type "Lakehouse"
      }

      Write-Host "All workspaces processed (created if missing; RBAC ensured)."








          - task: PowerShell@2
  displayName: 'Create Fabric workspaces for all sources from config'
  inputs:
    targetType: 'inline'
    script: |
      $ErrorActionPreference = 'Stop'

      $fabPath    = "C:\Program Files\Python312\Scripts\fab.exe"
      $configPath = "$(Build.SourcesDirectory)\infra\workspaces.json"

      if (-not (Test-Path $configPath)) { throw "Config file not found: $configPath" }

      # helper: idempotently ensure Admins (UPN or SPN objectId)
      function Ensure-WorkspaceAdmins {
        param([string]$WorkspaceName, [string[]]$Admins)
        if (-not $Admins -or $Admins.Count -eq 0) { return }
        $Admins = $Admins | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ } | Select-Object -Unique
        foreach ($a in $Admins) {
          Write-Host "    - ensuring Admin '$a' on '$WorkspaceName'..."
          & $fabPath acl set "$WorkspaceName.Workspace" -I $a -R admin -f
          if ($LASTEXITCODE -ne 0) {
            Write-Warning "      fab acl set failed for '$a' (exit $LASTEXITCODE) — continuing"
          }
        }
      }

      # 1) Snapshot existing workspace names via 'fab ls'
      Write-Host "Fetching existing workspaces using 'fab ls'..."
      $lsOutput = & $fabPath ls 2>&1
      $existingNames = $lsOutput |
        Where-Object { $_ -match '\.Workspace\s*$' } |
        ForEach-Object { ($_ -split '\.Workspace')[0].Trim() }

      # 2) Load JSON config (array of objects)
      $workspaces = Get-Content $configPath -Raw | ConvertFrom-Json
      $workspaces = @($workspaces)   # force array

      # optional: small helper to make folders/lakehouses
      function New-FabItem {
        param([string]$Path, [string]$Type)  # e.g. ws.Workspace/Lakehouses/bronze + Lakehouse
        Write-Host "    - Creating $Type '$Path.$Type'..."
        & $fabPath create "$Path.$Type"
        if ($LASTEXITCODE -ne 0) { throw "Failed to create $Type '$Path' (exit $LASTEXITCODE)." }
      }

      for ($i = 0; $i -lt $workspaces.Count; $i++) {
        $ws = $workspaces[$i]

        $name     = [string]$ws.workspaceName
        $source   = [string]$ws.source
        $capacity = [string]$ws.capacityName

        # accept adminObjectIds (array) or legacy adminObjectId (string)
        $admins = @()
        if ($ws.PSObject.Properties.Name -contains 'adminObjectIds' -and $ws.adminObjectIds) {
          $admins += @($ws.adminObjectIds)
        } elseif ($ws.PSObject.Properties.Name -contains 'adminObjectId' -and $ws.adminObjectId) {
          $admins += @("$($ws.adminObjectId)")
        }

        if ([string]::IsNullOrWhiteSpace($name))     { Write-Warning "Skipping index $i: no workspaceName"; continue }
        if ([string]::IsNullOrWhiteSpace($capacity)) { throw "capacityName is missing for workspace '$name'" }

        Write-Host "---------------------------------------------"
        Write-Host "Index       : $i"
        Write-Host "source      : $source"
        Write-Host "name        : '$name'"
        Write-Host "capacity    : $capacity"
        Write-Host "admins      : $($admins -join ', ')"

        # 3) If exists → DON'T skip; ensure RBAC (add any missing admins)
        if ($existingNames -contains $name) {
          Write-Host "  - Workspace exists → ensuring RBAC (adding any missing Admins)…"
          Ensure-WorkspaceAdmins -WorkspaceName $name -Admins $admins
          continue
        }

        # 4) If not exists → create, then set admins
        Write-Host "  - Creating workspace '$name' on capacity '$capacity'..."
        & $fabPath create "$name.Workspace" -P "capacityname=$capacity"
        if ($LASTEXITCODE -ne 0) { throw "Failed to create workspace '$name' (exit $LASTEXITCODE)" }

        Write-Host "  - Setting Admins on new workspace..."
        Ensure-WorkspaceAdmins -WorkspaceName $name -Admins $admins

        # 5) Create default folder + lakehouse structure
        Write-Host "  - Creating default folder & lakehouse structure in '$name'..."
        New-FabItem -Path "$name.Workspace/Pipelines"   -Type "Folder"
        New-FabItem -Path "$name.Workspace/Notebooks"   -Type "Folder"
        New-FabItem -Path "$name.Workspace/Scripts"     -Type "Folder"
        New-FabItem -Path "$name.Workspace/Lakehouses"  -Type "Folder"
        New-FabItem -Path "$name.Workspace/Lakehouses/bronze" -Type "Lakehouse"
        New-FabItem -Path "$name.Workspace/Lakehouses/silver" -Type "Lakehouse"
        New-FabItem -Path "$name.Workspace/Lakehouses/gold"   -Type "Lakehouse"
      }

      Write-Host "All workspaces processed; RBAC ensured for each."

