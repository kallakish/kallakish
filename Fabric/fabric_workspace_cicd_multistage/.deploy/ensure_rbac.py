#!/usr/bin/env python3
"""
Ensure Admins on Fabric/Power BI workspaces.
- Accepts users (UPN) and service principals (Enterprise App objectId GUID).
- Adds missing Admins (idempotent).
- Input file: your existing workspaces.json.
  Each entry may have:
    {
      "workspaceName": "...",            # or "workspaceId": "<guid>"
      "adminObjectIds": ["guid-or-upn", ...]  # preferred (array)
      # legacy: "adminObjectId": "single-guid-or-upn"
    }

Env:
  WORKSPACE_RBAC_FILE  (default: workspaces.json)
  WORKSPACE_FILTER     (optional: workspaceName to process only that one)
  TENANT_ID, CLIENT_ID, CLIENT_SECRET (optional; else DefaultAzureCredential)
"""
import os, json, re, sys, requests
from typing import Dict, List
from azure.identity import DefaultAzureCredential, ClientSecretCredential

GUID = re.compile(r"^[0-9a-fA-F-]{8}-[0-9a-fA-F-]{4}-[0-9a-fA-F-]{4}-[0-9a-fA-F-]{4}-[0-9a-fA-F-]{12}$")

def _cred():
    tid, cid, sec = os.getenv("TENANT_ID"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")
    return ClientSecretCredential(tid, cid, sec) if (tid and cid and sec) else DefaultAzureCredential(exclude_interactive_browser_credential=True)

def _token(scope="https://analysis.windows.net/powerbi/api/.default"):
    return _cred().get_token(scope).token

def _H():  # headers
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}

def list_groups() -> List[Dict]:
    r = requests.get("https://api.powerbi.com/v1.0/myorg/groups?$top=5000", headers=_H())
    r.raise_for_status()
    return r.json().get("value", [])

def gid_by(entry: Dict) -> str:
    if entry.get("workspaceId"):
        return entry["workspaceId"]
    name = entry.get("workspaceName")
    if not name:
        raise SystemExit("Each item must have workspaceName or workspaceId")
    for g in list_groups():
        if g.get("name") == name:
            return g["id"]
    raise SystemExit(f"Workspace not found by name: {name}")

def list_group_users(gid: str) -> List[Dict]:
    r = requests.get(f"https://api.powerbi.com/v1.0/myorg/groups/{gid}/users", headers=_H())
    r.raise_for_status()
    return r.json().get("value", [])

def add_admin(gid: str, ident: str):
    principalType = "App" if GUID.match(ident) else "User"
    body = {"identifier": ident, "groupUserAccessRight": "Admin", "principalType": principalType}
    r = requests.post(f"https://api.powerbi.com/v1.0/myorg/groups/{gid}/users", headers=_H(), json=body)
    if r.status_code in (200, 201, 409):  # 409 = already present (possibly with role)
        return
    r.raise_for_status()

def ensure_admins(entry: Dict):
    gid = gid_by(entry)
    # collect admins from either adminObjectIds[] or legacy adminObjectId
    admins = entry.get("adminObjectIds") or []
    if not admins and entry.get("adminObjectId"):
        admins = [entry["adminObjectId"]]
    admins = [str(a).strip() for a in admins if str(a).strip()]
    if not admins:
        return

    current = list_group_users(gid)
    have = set((u.get("identifier") or u.get("emailAddress") or "").lower() for u in current)

    name = entry.get("workspaceName", gid)
    for a in admins:
        if a.lower() not in have:
            print(f"[{name}] add Admin: {a}")
            add_admin(gid, a)

def main():
    path = os.getenv("WORKSPACE_RBAC_FILE", "workspaces.json")
    filt = (os.getenv("WORKSPACE_FILTER") or "").strip().lower()

    try:
        rows = json.loads(open(path, "r", encoding="utf-8").read())
    except FileNotFoundError:
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    if isinstance(rows, dict):
        rows = [rows]

    for row in rows:
        # filter by workspaceName if requested
        name = (row.get("workspaceName") or "").strip().lower()
        if filt and name != filt:
            continue
        ensure_admins(row)

    print("Workspace RBAC ensure complete.")

if __name__ == "__main__":
    main()
