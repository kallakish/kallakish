import msal
import os
import jwt
import sys

client_id = os.environ.get('FABRIC_CLIENT_ID')
tenant_id = os.environ.get('FABRIC_TENANT_ID')
client_secret = os.environ.get('FABRIC_CLIENT_SECRET')

app = msal.ConfidentialClientApplication(
    client_id,
    authority=f'https://login.microsoftonline.com/{tenant_id}',
    client_credential=client_secret,
)
result = app.acquire_token_for_client(scopes=['https://analysis.windows.net/powerbi/api/.default'])

token = result.get('access_token')
if not token:
    print('Failed to acquire token:', result)
    sys.exit(1)

decoded = jwt.decode(token, options={'verify_signature': False}, algorithms=['RS256'])

for k, v in decoded.items():
    print(f'{k}: {v}')
