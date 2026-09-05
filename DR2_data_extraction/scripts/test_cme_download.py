"""Temporary read-only test of one entitled CME DataMine file."""

import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
TOKEN_URL = "https://auth.cmegroup.com/as/token.oauth2"
FILE_URL = "https://datamine.new.cmegroup.com/cme/api/v2/download?fid=20260901-DLYBLLTN_DB_PRELIM_0_0"


def load_env() -> None:
    for line in (ROOT.parent / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


load_env()
basic = base64.b64encode(f"{os.environ['CME_API_ID']}:{os.environ['CME_API_KEY']}".encode()).decode()
token_request = Request(TOKEN_URL, data=b"grant_type=client_credentials", headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
with urlopen(token_request, timeout=30) as response:
    token = json.loads(response.read())["access_token"]

file_request = Request(FILE_URL, headers={"Authorization": f"Bearer {token}"})
with urlopen(file_request, timeout=60) as response:
    sample = response.read(5)
    print(f"HTTP {response.status}: download authorized")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {response.headers.get('Content-Length')}")
    print(f"PDF signature present: {sample == b'%PDF-'}")
    print("No file saved.")
