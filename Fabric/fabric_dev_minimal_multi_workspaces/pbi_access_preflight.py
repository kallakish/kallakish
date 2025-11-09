#!/usr/bin/env python3
"""
Preflight for Fabric/Power BI API access using a service principal.

- Reads FABRIC_CLIENT_ID / FABRIC_CLIENT_SECRET / FABRIC_TENANT_ID from env
- Takes --workspace-id (or uses env FABRIC_WORKSPACE_ID[_DEV])
- Prints token claims (aud, tid, appid, roles/scp)
- Calls both GET /v1.0/myorg/groups/{id} and GET /v1/workspaces/{id}
- Optionally calls RefreshUserPermissions and retries (--refresh)
- Sets Azure DevOps variable `workspace_id_clean` for downstream steps

Exit codes:
  0 = success (200 from at least one endpoint)
  2 = invalid workspace id
  3 = token acquisition failure
  4 = access still denied after optional refresh
  5 = missing required environment variables
"""

import os, sys, re, time, argparse, json
import requests
import msal
import jwt

PBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"

def eprint(*a, **k): print(*a, file=sys.stderr, **k)

def sanitize_guid(raw: str) -> str:
    cleaned = "".join(ch for ch in (raw or "") if ch in "0123456789abcdefABCDEF-")
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", cleaned or ""):
        eprint(f"[ERROR] Workspace ID invalid after cleanup: '{raw}' -> '{cleaned}'")
        sys.exit(2)
    return cleaned

def acquire_token(tenant: str, client_id: str, client_secret: str) -> str:
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=[PBI_SCOPE])
    if not result or "access_token" not in result:
        eprint("[ERROR] Failed to get token:", json.dumps(result, indent=2))
        sys.exit(3)
    return result["access_token"]

def print_claims(tok: str) -> None:
    header = jwt.get_unverified_header(tok)
    claims = jwt.decode(tok, options={"verify_signature": False, "verify_aud": False})
    interesting = {k: claims.get(k) for k in ("aud","iss","tid","appid","roles","scp")}
    print("== token header ==", json.dumps({k: header.get(k) for k in ("typ","alg","kid")}, indent=2))
    print("== token claims ==", json.dumps(interesting, indent=2))

def get_json(url: str, token: str) -> requests.Response:
    return requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)

def post_json(url: str, token: str) -> requests.Response:
    return requests.post(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)

def probe_workspace(workspace_id: str, token: str) -> tuple[int,int]:
    url_groups = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    url_worksp = f"https://api.powerbi.com/v1/workspaces/{workspace_id}"

    r1 = get_json(url_groups, token)
    print(f"GET {url_groups} -> {r1.status_code}")
    if r1.status_code != 200:
        print("  body:", (r1.text or "").replace("\n"," ")[:300])

    r2 = get_json(url_worksp, token)
    print(f"GET {url_worksp} -> {r2.status_code}")
    if r2.status_code != 200:
        print("  body:", (r2.text or "").replace("\n"," ")[:300])

    return r1.status_code, r2.status_code

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-id", help="Workspace GUID")
    ap.add_argument("--refresh", action="store_true", help="Call RefreshUserPermissions and retry once")
    args = ap.parse_args()

    client_id = os.getenv("FABRIC_CLIENT_ID")
    tenant_id = os.getenv("FABRIC_TENANT_ID")
    client_secret = os.getenv("FABRIC_CLIENT_SECRET")
    if not all([client_id, tenant_id, client_secret]):
        eprint("[ERROR] Missing env vars: FABRIC_CLIENT_ID / FABRIC_TENANT_ID / FABRIC_CLIENT_SECRET")
        sys.exit(5)

    wid_raw = args.workspace_id or os.getenv("FABRIC_WORKSPACE_ID") or os.getenv("FABRIC_WORKSPACE_ID_DEV")
    if not wid_raw:
        eprint("[ERROR] Provide --workspace-id or set FABRIC_WORKSPACE_ID[_DEV]")
        sys.exit(2)

    print(f"WorkspaceId (raw): {wid_raw}")
    wid = sanitize_guid(wid_raw)
    print(f"WorkspaceId (clean): {wid}")
    # Export for Azure DevOps
    print(f"##vso[task.setvariable variable=workspace_id_clean]{wid}")

    token = acquire_token(tenant_id, client_id, client_secret)
    print_claims(token)

    s1, s2 = probe_workspace(wid, token)
    if s1 == 200 or s2 == 200:
        print("[OK] Power BI API access confirmed.")
        sys.exit(0)

    if args.refresh:
        print("Calling RefreshUserPermissions and retrying in ~60s...")
        r = post_json("https://api.powerbi.com/v1.0/myorg/RefreshUserPermissions", token)
        print("RefreshUserPermissions ->", r.status_code, (r.text or "")[:200])
        time.sleep(60)
        s1, s2 = probe_workspace(wid, token)
        if s1 == 200 or s2 == 200:
            print("[OK] Access succeeded after refresh.")
            sys.exit(0)

    eprint("[FAIL] Still not authorized to read the workspace.")
    eprint("       Ensure the SPN is Workspace Admin/Member and the tenant setting")
    eprint("       'Allow service principals to use Power BI APIs' includes this SPN (via a security group).")
    sys.exit(4)

if __name__ == "__main__":
    main()
