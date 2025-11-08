# Install module if needed
# Install-Module AzureAD

# Log in interactively
Connect-AzureAD

# Set your values here
$appName = "<Your-App-Registration-Name>" # Replace with your app registration name
$powerBIAppId = "00000009-0000-0000-c000-000000000000" # Power BI API App ID

# Get App Registration and Power BI Service Principal
$app = Get-AzureADApplication -Filter "DisplayName eq '$appName'"
$sp = Get-AzureADServicePrincipal -Filter "AppId eq '$powerBIAppId'"

# Delegated permission GUID for Workspace.ReadWrite.All
$workspaceReadWriteAllId = "9b29c84f-44fb-4b1c-8186-963b4f4f2ea6"

# Add delegated Power BI API permission to app registration
$resourceAccess = New-Object -TypeName "Microsoft.Open.AzureAD.Model.ResourceAccess"
$resourceAccess.Id = $workspaceReadWriteAllId
$resourceAccess.Type = "Scope"

$requiredResourceAccess = New-Object -TypeName "Microsoft.Open.AzureAD.Model.RequiredResourceAccess"
$requiredResourceAccess.ResourceAppId = $powerBIAppId
$requiredResourceAccess.ResourceAccess = @($resourceAccess)

# Combine with existing permissions if present
$appPerms = $app.RequiredResourceAccess
$newPerms = $appPerms + $requiredResourceAccess

Set-AzureADApplication -ObjectId $app.ObjectId -RequiredResourceAccess $newPerms

Write-Host "Delegated permission Workspace.ReadWrite.All added to app registration $appName."

# NOTE: Granting admin consent for delegated permissions must be done from the Azure Portal (App Registration > API Permissions > Grant admin consent for <Directory>) OR via Microsoft Graph API endpoints.
