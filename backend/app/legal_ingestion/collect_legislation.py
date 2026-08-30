"""Resumable official-source legislation collector for VeriDoc.

The collector accepts a JSONL seed file of official document URLs, downloads
records with retries, follows redirects, computes SHA-256, and writes a
manifest. It deliberately does not infer legal metadata from filenames.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[2]
SEED_FILE = ROOT / "data" / "legal_corpus" / "manifests" / "legislation_seeds.jsonl"
MANIFEST_FILE = ROOT / "data" / "legal_corpus" / "manifests" / "legislation_downloads.jsonl"
RAW_DIR = ROOT / "data" / "legal_corpus" / "acts" / "raw"

USER_AGENT = "VeriDoc-Research-Prototype/0.1 (+source-grounded legal QA)"
TIMEOUT = 45
RETRIES = 3


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_existing() -> dict[str, dict]:
    records = {}
    if MANIFEST_FILE.exists():
        for line in MANIFEST_FILE.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                item = json.loads(line)
                records[item["seed_url"]] = item
    return records


def append_record(item: dict) -> None:
    with MANIFEST_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")


def download(seed: dict, existing: dict[str, dict]) -> None:
    seed_url = seed["source_url"]
    if seed_url in existing and existing[seed_url].get("status") == "downloaded":
        print(f"SKIP {seed_url}")
        return

    parsed = urlparse(seed_url)
    suffix = Path(parsed.path).suffix.lower() or ".bin"
    filename = hashlib.sha256(seed_url.encode()).hexdigest()[:20] + suffix
    target = RAW_DIR / filename
    error = ""

    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.get(
                seed_url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()
            target.write_bytes(response.content)
            item = {
                **seed,
                "seed_url": seed_url,
                "final_url": response.url,
                "retrieved_at": now(),
                "status": "downloaded",
                "http_status": response.status_code,
                "sha256": sha256(target ),
                "local_path": str(target.relative_to(ROOT)),
                "bytes": target.stat().st_size,
                "attempts": attempt,
            }
            append_record(item)
            existing[seed_url] = item
            print(f"OK {seed_url} -> {target.name}")
            return
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            time.sleep(attempt)

    item = {**seed, "seed_url": seed_url, "retrieved_at": now(), "status": "error", "error": error}
    append_record(item)
    existing[seed_url] = item
    print(f"ERROR {seed_url}: {error}")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing()
    if not SEED_FILE.exists():
        print(f"Missing seed file: {SEED_FILE}")
        return
    seeds = [json.loads(line) for line in SEED_FILE.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    print(f"Seeds: {len(seeds)} | Existing records: {len(existing)}")
    for seed in seeds:
        download(seed, existing)


if __name__ == "__main__":
    main()

