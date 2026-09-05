#!/usr/bin/env python3
"""Read-only CME DataMine authentication and entitlement-list test."""

import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT.parent / ".env"
LIST_ENDPOINT = "https://datamine.new.cmegroup.com/api/list_entitlements_files"
TOKEN_ENDPOINT = "https://auth.cmegroup.com/as/token.oauth2"


def load_dotenv() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def main() -> int:
    load_dotenv()
    api_id = os.getenv("CME_API_ID")
    api_key = os.getenv("CME_API_KEY")
    if not api_id or not api_key:
        print("FAIL: CME_API_ID and CME_API_KEY must be set")
        return 2

    auth = base64.b64encode(f"{api_id}:{api_key}".encode()).decode()
    token_request = Request(
        TOKEN_ENDPOINT,
        data=urlencode({"grant_type": "client_credentials"}).encode(),
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "GoldRush2 CME DataMine test",
        },
        method="POST",
    )
    try:
        with urlopen(token_request, timeout=30) as response:
            token_data = json.loads(response.read().decode("utf-8"))
        access_token = token_data["access_token"]
    except HTTPError as exc:
        detail = exc.read(300).decode("utf-8", errors="replace")
        print(f"FAIL: CME token request returned HTTP {exc.code}: {detail}")
        return 1
    except (URLError, json.JSONDecodeError, KeyError) as exc:
        print(f"FAIL: CME token request failed: {exc}")
        return 1

    request = Request(
        f"{LIST_ENDPOINT}?{urlencode({'dataset_code': 'DLYBLLTN_DB', 'limit': 10})}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "GoldRush2 CME DataMine test",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(f"HTTP {response.status}: authentication succeeded")
    except HTTPError as exc:
        detail = exc.read(300).decode("utf-8", errors="replace")
        print(f"FAIL: CME returned HTTP {exc.code}: {detail}")
        return 1
    except URLError as exc:
        print(f"FAIL: network error: {exc.reason}")
        return 1
    except json.JSONDecodeError:
        print("FAIL: CME response was not valid JSON")
        return 1

    records = data.get("data", []) if isinstance(data, dict) else []
    if isinstance(data, dict):
        print(f"Response keys: {', '.join(sorted(data.keys()))}")
    files = [file for record in records for file in record.get("files", [])]
    print(f"Entitlement records: {len(records)}")
    print(f"Files returned: {len(files)}")
    for file in files[:5]:
        print(f"file_id: {file.get('file_id')} | file_name: {file.get('file_name')}")
    print("No file was downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
