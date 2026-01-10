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

# Use .NET serializer (more reliable than ConvertTo-Json in Windows PowerShell 5.1)
Add-Type -AssemblyName System.Web.Extensions

$json = Get-Content -Path $InTemplate -Raw -Encoding UTF8

$ser = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$ser.MaxJsonLength = 2147483647
$ser.RecursionLimit = 10000

$template = $ser.DeserializeObject($json)

if (-not $template.ContainsKey("resources")) {
  throw "ARM template does not contain a 'resources' array. Check the input file: $InTemplate"
}

$before = $template["resources"].Count

# Filter out IR resources
$template["resources"] = @(
  $template["resources"] | Where-Object {
    $_["type"] -ne "Microsoft.DataFactory/factories/integrationRuntimes" -and
    $_["type"] -ne "Microsoft.DataFactory/factories/integrationruntimes"
  }
)

$after = $template["resources"].Count
Write-Host "Removed $($before - $after) Integration Runtime resources"

$outJson = $ser.Serialize($template)

# Write UTF8 without BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($OutTemplate, $outJson, $utf8NoBom)

Write-Host "Wrote patched template to: $OutTemplate"

