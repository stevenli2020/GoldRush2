"""Read-only inspection of CME DataMine datasets entitled to this API ID."""

import base64
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
TOKEN_URL = "https://auth.cmegroup.com/as/token.oauth2"
LIST_URL = "https://datamine.new.cmegroup.com/api/list_entitlements_files"


def load_env() -> None:
    for line in (ROOT.parent / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def main() -> None:
    load_env()
    basic = base64.b64encode(f"{os.environ['CME_API_ID']}:{os.environ['CME_API_KEY']}".encode()).decode()
    token_request = Request(TOKEN_URL, data=b"grant_type=client_credentials", headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urlopen(token_request, timeout=30) as response:
        token = json.loads(response.read())["access_token"]

    request = Request(f"{LIST_URL}?{urlencode({'limit': 1000})}", headers={"Authorization": f"Bearer {token}"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read())

    records = payload.get("data", [])
    print(f"HTTP {response.status}: authenticated")
    print(f"Entitlement records returned: {len(records)}")
    for record in records:
        files = record.get("files", [])
        print(f"dataset_code={record.get('dataset_code')} | dataset_name={record.get('dataset_name')} | files={len(files)}")


if __name__ == "__main__":
    main()
