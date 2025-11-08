$tenantId = "<your-tenant-id>"
$clientId = "<your-client-id>"
$clientSecret = "<your-client-secret>"
$scope = "https://analysis.windows.net/powerbi/api/.default"
$tokenUrl = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"

$body = @{
    client_id     = $clientId
    client_secret = $clientSecret
    scope         = $scope
    grant_type    = "client_credentials"
}

$response = Invoke-RestMethod -Method POST -Uri $tokenUrl -ContentType "application/x-www-form-urlencoded" -Body $body
Write-Host "Status code:" $response.StatusCode
Write-Host "Access Token:" $response.access_token
Write-Host "Full Response:" ($response | ConvertTo-Json -Depth 10)




# Install module if needed
# Install-Module AzureAD

# Log in interactively
Write-Host "Connecting to Azure AD..."
Connect-AzureAD
Write-Host "Connected to Azure AD."

# Set your app registration and API details
$appName = "<Your-App-Registration-Name>"  # Replace with your app registration name
$powerBIAppId = "00000009-0000-0000-c000-000000000000" # Power BI API App ID
Write-Host "App registration name: $appName"

Try {
    Write-Host "Getting Azure AD Application..."
    $app = Get-AzureADApplication -Filter "DisplayName eq '$appName'"
    Write-Host "App found: $($app.AppId)"
} Catch {
    Write-Host "Failed to get Azure AD Application: $_"
}

Try {
    Write-Host "Getting Power BI Service Principal..."
    $sp = Get-AzureADServicePrincipal -Filter "AppId eq '$powerBIAppId'"
    Write-Host "Power BI SP found: $($sp.ObjectId)"
} Catch {
    Write-Host "Failed to get Power BI Service Principal: $_"
}

# Delegated permission GUID for Workspace.ReadWrite.All
$workspaceReadWriteAllId = "9b29c84f-44fb-4b1c-8186-963b4f4f2ea6"
Write-Host "Delegated permission ID for Workspace.ReadWrite.All: $workspaceReadWriteAllId"

Try {
    Write-Host "Building resource access object..."
    $resourceAccess = New-Object -TypeName "Microsoft.Open.AzureAD.Model.ResourceAccess"
    $resourceAccess.Id = $workspaceReadWriteAllId
    $resourceAccess.Type = "Scope"
    Write-Host "Resource access object built."
} Catch {
    Write-Host "Failed when building resource access object: $_"
}

Try {
    Write-Host "Building required resource access object..."
    $requiredResourceAccess = New-Object -TypeName "Microsoft.Open.AzureAD.Model.RequiredResourceAccess"
    $requiredResourceAccess.ResourceAppId = $powerBIAppId
    $requiredResourceAccess.ResourceAccess = @($resourceAccess)
    Write-Host "Required resource access object built."
} Catch {
    Write-Host "Failed when building required resource access object: $_"
}

Try {
    Write-Host "Getting existing app permissions..."
    $appPerms = $app.RequiredResourceAccess
    Write-Host "Existing app permissions loaded."
} Catch {
    Write-Host "Failed to get existing permissions: $_"
}

Try {
    Write-Host "Combining new and existing permissions..."
    $newPerms = $appPerms + $requiredResourceAccess
    Write-Host "Permissions combined."
} Catch {
    Write-Host "Failed when combining permissions: $_"
}

Try {
    Write-Host "Applying new permissions to the app registration..."
    Set-AzureADApplication -ObjectId $app.ObjectId -RequiredResourceAccess $newPerms
    Write-Host "Delegated permission Workspace.ReadWrite.All added to app registration $appName."
} Catch {
    Write-Host "Failed when setting permissions: $_"
}

