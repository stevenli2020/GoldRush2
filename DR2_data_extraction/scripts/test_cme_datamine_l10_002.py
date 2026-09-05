"""Temporary, read-only CME DataMine entitlement test for L10-002."""

from __future__ import annotations

import os
import sys
import base64
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
LIST_URL = "https://datamine.new.cmegroup.com/api/list_entitlements_files"


def load_dotenv() -> None:
    env_path = ROOT.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"\''))


def main() -> int:
    load_dotenv()
    api_id = os.getenv("CME_API_ID")
    api_key = os.getenv("CME_API_KEY")
    if not api_id or not api_key:
        print("FAIL: CME_API_ID and CME_API_KEY must both be configured")
        return 2

    credentials = base64.b64encode(f"{api_id}:{api_key}".encode()).decode()
    params = {"category_code": "EOD", "exchange_code": "XCEC", "product_code": "GC", "limit": "1000"}
    request = Request(
        f"{LIST_URL}?{urlencode(params)}",
        headers={"Authorization": f"Basic {credentials}", "User-Agent": "GoldRush2 temporary CME test"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read()
            status = response.status
    except HTTPError as exc:
        detail = exc.read(300).decode("utf-8", errors="replace")
        print(f"FAIL: CME returned HTTP {exc.code}: {detail}")
        return 1
    except URLError as exc:
        print(f"FAIL: CME request could not be completed: {exc.reason}")
        return 1

    print(f"HTTP {status}: authenticated request succeeded")
    print(f"Response bytes: {len(body)}")
    print("The response was intentionally not saved or printed because it may contain entitled file metadata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
