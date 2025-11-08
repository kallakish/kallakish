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
