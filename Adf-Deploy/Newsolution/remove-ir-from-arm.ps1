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
