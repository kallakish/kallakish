# set_varlib_active.py
import os, sys, requests

tenant  = os.environ["FABRIC_TENANT_ID"]
client  = os.environ["FABRIC_CLIENT_ID"]
secret  = os.environ["FABRIC_CLIENT_SECRET"]
wsid    = os.environ["FABRIC_WORKSPACE_ID"]      # target workspace
libname = os.environ["FABRIC_VARLIB_NAME"]       # e.g., MDF_Lib
target  = os.environ["TARGET_VALUE_SET"]         # Dev | Test | UAT | Prod

# 1) get Fabric API token
tok = requests.post(
    f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
    data={
        "grant_type": "client_credentials",
        "client_id": client,
        "client_secret": secret,
        "scope": "https://api.fabric.microsoft.com/.default",
    },
    timeout=30,
).json()["access_token"]
hdr = {"Authorization": f"Bearer {tok}"}

# 2) find the library by name
libs = requests.get(
    f"https://api.fabric.microsoft.com/v1/workspaces/{wsid}/VariableLibraries",
    headers=hdr, timeout=60
).json().get("value", [])

match = [l for l in libs if (l.get("displayName") or l.get("name")) == libname]
if not match:
    print(f"[ERROR] Variable Library '{libname}' not found in workspace {wsid}", file=sys.stderr)
    sys.exit(2)
lib = match[0]

# 3) set active value-set
requests.patch(
    f"https://api.fabric.microsoft.com/v1/workspaces/{wsid}/VariableLibraries/{lib['id']}",
    headers={**hdr, "Content-Type": "application/json"},
    json={"properties": {"activeValueSetName": target}},
    timeout=60
).raise_for_status()

print(f"[OK] Active value-set set to '{target}' for '{libname}' (workspace {wsid})")






Post deployment : # After you publish VariableLibrary + Pipelines for that env
- script: |
    "C:/Program Files/Python312/python.exe" azure-pipelines/.deploy/set_varlib_active.py
  displayName: "Activate Variable Library value-set"
  env:
    FABRIC_CLIENT_ID:     $(FABRIC_CLIENT_ID)
    FABRIC_TENANT_ID:     $(FABRIC_TENANT_ID)
    FABRIC_CLIENT_SECRET: $(FABRIC_CLIENT_SECRET)
    FABRIC_WORKSPACE_ID:  $(FABRIC_WORKSPACE_ID_TEST)   # set per stage
    FABRIC_VARLIB_NAME:   MDF_Lib                       # your library display name
    TARGET_VALUE_SET:     Test             
