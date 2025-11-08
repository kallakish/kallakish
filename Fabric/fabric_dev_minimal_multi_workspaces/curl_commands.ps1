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




# Acquire token as before
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
$jwt = $response.access_token

# Decode JWT token and print 'roles' claim
$tokenParts = $jwt -split '\.'
$payload = $tokenParts[1]
# Pad with '=' signs if needed for base64 decoding
$payload = $payload + ('=' * (4 - ($payload.Length % 4)))
$decoded = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload))
$claims = $decoded | ConvertFrom-Json

if ($claims.roles) {
    Write-Host "Roles in token:"
    $claims.roles
} else {
    Write-Host "No 'roles' claim found in the token."
}

