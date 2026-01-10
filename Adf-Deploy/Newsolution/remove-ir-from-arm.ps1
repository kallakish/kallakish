param(
  [Parameter(Mandatory=$true)][string]$InTemplate,
  [Parameter(Mandatory=$true)][string]$OutTemplate
)

$template = Get-Content $InTemplate -Raw | ConvertFrom-Json

# Remove Integration Runtime resources
$template.resources = @($template.resources | Where-Object {
  $_.type -ne "Microsoft.DataFactory/factories/integrationRuntimes" -and
  $_.type -ne "Microsoft.DataFactory/factories/integrationruntimes"
})

$template | ConvertTo-Json -Depth 200 | Set-Content $OutTemplate


#if we get a json erro use below :

param(
  [Parameter(Mandatory=$true)][string]$InTemplate,
  [Parameter(Mandatory=$true)][string]$OutTemplate
)

# Find python (try python, then py -3)
$python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue)?.Source }

if (-not $python) {
  throw "Python not found on the agent. Install Python or use a Microsoft-hosted windows agent. (Tried: python, py)"
}

# Python code to:
# 1) Remove IR resources
# 2) Remove dependsOn entries that reference integrationRuntimes (prevents broken dependsOn)
$code = @"
import json, sys

in_path = sys.argv[1]
out_path = sys.argv[2]

with open(in_path, "r", encoding="utf-8") as f:
    doc = json.load(f)

def is_ir(res):
    t = (res or {}).get("type", "")
    return isinstance(t, str) and t.lower() == "microsoft.datafactory/factories/integrationruntimes"

def patch_res(res):
    if isinstance(res, dict):
        # Remove dependsOn references to IR
        dep = res.get("dependsOn")
        if isinstance(dep, list):
            res["dependsOn"] = [d for d in dep if isinstance(d, str) and "integrationruntimes" not in d.lower()]

        # Recurse into nested resources if any
        if isinstance(res.get("resources"), list):
            res["resources"] = [patch_res(r) for r in res["resources"] if not is_ir(r)]
    return res

resources = doc.get("resources", [])
if isinstance(resources, list):
    before = len(resources)
    resources = [patch_res(r) for r in resources if not is_ir(r)]
    after = len(resources)
    doc["resources"] = resources
    print(f"Removed {before-after} integrationRuntime resources")
else:
    print("No top-level resources array found (unexpected for ARM template)")

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
"@

# Execute python (supports both python.exe and py.exe)
if ($python.ToLower().EndsWith("py.exe")) {
  & $python -3 -c $code $InTemplate $OutTemplate
} else {
  & $python -c $code $InTemplate $OutTemplate
}

if ($LASTEXITCODE -ne 0) {
  throw "Python patch failed with exit code $LASTEXITCODE"
}

Write-Host "Patched template written to: $OutTemplate"


