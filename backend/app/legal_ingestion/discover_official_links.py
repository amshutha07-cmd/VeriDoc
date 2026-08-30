import json
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

queue = Path("backend/data/legal_corpus/manifests/official_source_queue.jsonl")
out = Path("backend/data/legal_corpus/manifests/discovered_official_links.jsonl")
headers = {"User-Agent": "VeriDoc-Research-Prototype/0.1"}
rows = []
for line in queue.read_text(encoding="utf-8-sig").splitlines():
    if not line.strip():
        continue
    item = json.loads(line)
    try:
        r = requests.get(item["source_url"], headers=headers, timeout=30, allow_redirects=True)
        print(r.status_code, r.url)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(r.url, a["href"])
            if ".pdf" in href.lower() or "download" in href.lower():
                rows.append({**item, "discovered_url": href, "link_text": a.get_text(" ", strip=True), "final_landing_url": r.url})
    except Exception as e:
        print("ERROR", item["source_url"], type(e).__name__, str(e))

unique = {x["discovered_url"]: x for x in rows}
out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in unique.values()) + ("\n" if unique else ""), encoding="utf-8")
print("discovered_links=", len(unique))
