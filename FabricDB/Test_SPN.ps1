# ===== CONFIGURE THESE =====
$tenantId    = "<your-tenant-id-guid>"
$clientId    = "<your-spn-application-client-id-guid>"
$clientSecret = "<your-spn-client-secret-VALUE>"  # VALUE, not secret ID
$sqlServer   = "<your-fabric-sql-server>.database.windows.net"
$sqlDb       = "<your-fabric-sql-db-name>"
# ===========================

# 1) Get an AAD access token for Azure SQL (resource = https://database.windows.net/)
$tokenEndpoint = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"
$body = @{
    client_id     = $clientId
    client_secret = $clientSecret
    grant_type    = "client_credentials"
    scope         = "https://database.windows.net/.default"
}

Write-Host "Requesting access token for SPN..."
$response = Invoke-RestMethod -Uri $tokenEndpoint -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
$accessToken = $response.access_token

if (-not $accessToken) {
    Write-Error "❌ Could not obtain access token for the service principal."
    return
}

Write-Host "✅ Got access token."

# 2) Use System.Data.SqlClient with the token (no Authentication keyword in the connection string)
Add-Type -AssemblyName "System.Data"

$connString = "Server=tcp:$sqlServer,1433;Initial Catalog=$sqlDb;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"

$conn = New-Object System.Data.SqlClient.SqlConnection $connString
$conn.AccessToken = $accessToken

try {
    Write-Host "Attempting to open SQL connection with access token..."
    $conn.Open()
    Write-Host "✅ Successfully connected to Fabric SQL as the service principal."

    # Run a tiny test query
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT TOP (1) name FROM sys.objects"
    $result = $cmd.ExecuteScalar()
    Write-Host "Test query result: $result"
}
catch {
    Write-Host "❌ Failed to connect or query as SPN."
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host $_.Exception.ToString()
}
finally {
    if ($conn.State -eq 'Open') { $conn.Close() }
}
