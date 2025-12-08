#!/usr/bin/env python3
import os, re, json, sys, requests
from pathlib import Path
from azure.identity import DefaultAzureCredential, ClientSecretCredential

GUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")

def cred():
    tid, cid, sec = os.getenv("TENANT_ID"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")
    return (ClientSecretCredential(tid, cid, sec)
            if (tid and cid and sec)
            else DefaultAzureCredential(exclude_interactive_browser_credential=True))

def bearer(scope: str) -> str:
    return cred().get_token(scope).token

def get_capacity_arm(sub, rg, name):
    h = {"Authorization": f"Bearer {bearer('https://management.azure.com/.default')}"}
    url = f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Fabric/capacities/{name}?api-version=2025-01-15-preview"
    r = requests.get(url, headers=h)
    r.raise_for_status()
    return r.json(), url, h

def put_capacity_admins(existing_body, url, h, members):
    # keep existing location/sku; update admins
    body = {
        "location": existing_body["location"],
        "sku": existing_body["sku"],
        "properties": {"administration": {"members": members}}
    }
    r = requests.put(url, headers={**h, "Content-Type": "application/json"}, data=json.dumps(body))
    r.raise_for_status()
    return r.json()

def list_groups():
    h = {"Authorization": f"Bearer {bearer('https://analysis.windows.net/powerbi/api/.default')}"}
    r = requests.get("https://api.powerbi.com/v1.0/myorg/groups?$top=5000", headers=h)
    r.raise_for_status()
    return r.json().get("value", [])

def get_group_id_by_name(name: str) -> str:
    for g in list_groups():
        if g.get("name") == name:
            return g["id"]
    raise SystemExit(f"Workspace not found by name: {name}")

def list_group_users(group_id: str):
    h = {"Authorization": f"Bearer {bearer('https://analysis.windows.net/powerbi/api/.default')}"}
    r = requests.get(f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/users", headers=h)
    r.raise_for_status()
    return r.json().get("value", [])

def add_group_user_admin(group_id: str, identifier: str):
    h = {"Authorization": f"Bearer {bearer('https://analysis.windows.net/powerbi/api/.default')}",
         "Content-Type": "application/json"}
    principal_type = "App" if GUID_RE.match(identifier) else "User"
    body = {
        "identifier": identifier,                 # UPN (user) or SP objectId (App)
        "groupUserAccessRight": "Admin",
        "principalType": principal_type
    }
    r = requests.post(f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/users",
                      headers=h, data=json.dumps(body))
    if r.status_code in (200, 201):
        return
    if r.status_code == 409:
        # already exists with some role; caller might need to promote role manually
        return
    r.raise_for_status()

def ensure_capacity_admins_for_capacity(sub, rg, capacity_name, admin_identifiers):
    existing, url, h = get_capacity_arm(sub, rg, capacity_name)
    desired = list(dict.fromkeys(admin_identifiers))  # unique, keep order
    put_capacity_admins(existing, url, h, desired)

def ensure_workspace_admins(workspace_name, admin_identifiers):
    gid = get_group_id_by_name(workspace_name)
    current = list_group_users(gid)
    have = set()
    for u in current:
        # For users: 'identifier' is the UPN; for SP: there's 'principalType'=='App' and 'identifier' is objectId
        ident = u.get("identifier") or u.get("emailAddress") or u.get("displayName")
        if ident: have.add(ident.lower())
    for ident in admin_identifiers:
        key = ident.lower()
        if key not in have:
            add_group_user_admin(gid, ident)

def main():
    # inputs
    params_path = os.getenv("RBAC_PARAMS_FILE", "capacity-admins.json")
    sub = os.getenv("AZ_SUBSCRIPTION_ID")
    rg  = os.getenv("AZ_RESOURCE_GROUP")

    if not (sub and rg):
        print("ERROR: set AZ_SUBSCRIPTION_ID and AZ_RESOURCE_GROUP env vars", file=sys.stderr)
        sys.exit(2)

    rows = json.loads(Path(params_path).read_text(encoding="utf-8"))
    # Group rows by capacity to compute union of admins for each capacity
    admins_by_capacity = {}
    for r in rows:
        cap = r["capacityName"]
        admins_by_capacity.setdefault(cap, set()).update(r.get("adminObjectIds", []))

    # 1) ensure capacity admins
    for cap, admins in admins_by_capacity.items():
        print(f"[capacity] ensure admins for {cap}: {sorted(admins)}")
        ensure_capacity_admins_for_capacity(sub, rg, cap, sorted(admins))

    # 2) ensure workspace admins
    for r in rows:
        ws = r["workspaceName"]
        admins = r.get("adminObjectIds", [])
        print(f"[workspace] ensure admins for {ws}: {admins}")
        ensure_workspace_admins(ws, admins)

if __name__ == "__main__":
    main()
