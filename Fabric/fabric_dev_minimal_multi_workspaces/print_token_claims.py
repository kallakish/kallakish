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

print("Decoded Token Claims:")
for k, v in decoded.items():
    # Print roles, scp, wids with clear labels
    if k in ['roles', 'scp', 'wids']:
        print(f'{k}: {v}')
    else:
        # For other claims, print key and first 100 chars of value to keep it readable
        if isinstance(v, list):
            # Show list length and sample
            print(f'{k}: (list of length {len(v)}) {v[:3]}{"..." if len(v) > 3 else ""}')
        else:
            print(f'{k}: {str(v)[:100]}')

# Additionally show scopes and roles clearly if present separately
if 'scp' in decoded:
    print("\nScopes (scp):", decoded['scp'])
if 'roles' in decoded:
    print("Roles:", decoded['roles'])
if 'wids' in decoded:
    print("App Role IDs (wids):", decoded['wids'])
