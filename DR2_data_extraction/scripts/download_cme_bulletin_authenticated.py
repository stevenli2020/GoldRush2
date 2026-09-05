"""Download one entitled CME DataMine Daily Bulletin file."""
import base64, json, os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TOKEN_URL = "https://auth.cmegroup.com/as/token.oauth2"
FILE_ID = "20260901-DLYBLLTN_DB_PRELIM_0_0"
DOWNLOAD_URL = "https://datamine.new.cmegroup.com/cme/api/v2/download?fid=" + FILE_ID

for line in (ROOT.parent / ".env").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.lstrip().startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

credentials = base64.b64encode(f"{os.environ['CME_API_ID']}:{os.environ['CME_API_KEY']}".encode()).decode()
token_request = Request(TOKEN_URL, data=b"grant_type=client_credentials", headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
with urlopen(token_request, timeout=30) as response:
    token = json.loads(response.read())['access_token']
file_request = Request(DOWNLOAD_URL, headers={"Authorization": f"Bearer {token}", "User-Agent": "GoldRush2 CME DataMine"})
with urlopen(file_request, timeout=60) as response:
    content = response.read()
if not content.startswith(b"%PDF"):
    raise RuntimeError("Entitled response was not a PDF")
output = ROOT / "data" / "raw" / "cme" / f"{FILE_ID}.pdf"
output.parent.mkdir(parents=True, exist_ok=True)
temporary = output.with_suffix(".pdf.tmp")
temporary.write_bytes(content)
os.replace(temporary, output)
print(f"HTTP 200: downloaded {FILE_ID}")
print(f"Saved: {output}")
print(f"Bytes: {len(content)}")
