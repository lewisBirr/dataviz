"""
01_sample.py — Stratified sample from the Epstein Files parquet shards.

Downloads shards in parallel (WORKERS threads) via hf_hub_download, reads each
with polars, deletes it immediately, and stops as soon as all strata hit
SAMPLE_SIZE.

Usage:
    uv run python eda/01_sample.py
"""

import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from huggingface_hub import HfApi, hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eda.config import (
    CACHE_DIR,
    DATASET_NAME,
    HF_MAX_RETRIES,
    SAMPLE_PATH,
    SAMPLE_SIZE,
)

load_dotenv()

COLUMNS = ["dataset_id", "doc_id", "file_name", "file_type", "online_url", "text_content", "metadata"]
SHARD_DIR = CACHE_DIR / "_shards"
WORKERS = 1


def download_and_read(fname: str, token: str | None, attempt: int = 0) -> pl.DataFrame | None:
    try:
        local_path = hf_hub_download(
            repo_id=DATASET_NAME,
            filename=fname,
            repo_type="dataset",
            token=token,
            local_dir=str(SHARD_DIR),
            local_dir_use_symlinks=False,
        )
        df = pl.read_parquet(local_path, columns=COLUMNS)
        Path(local_path).unlink(missing_ok=True)
        return df
    except Exception as exc:
        if attempt >= HF_MAX_RETRIES - 1:
            print(f"   ❌ {fname} failed: {exc}", flush=True)
            return None
        time.sleep(2 ** attempt)
        return download_and_read(fname, token, attempt + 1)


def main() -> None:
    token = os.environ.get("HF_TOKEN") or None
    print(f"{'🔑 Using HF token.' if token else '🌐 No HF_TOKEN — expect rate limits.'}", flush=True)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    print("📋 Listing shards …", flush=True)
    api = HfApi(token=token)
    all_files = list(api.list_repo_files(DATASET_NAME, repo_type="dataset"))
    shards = sorted(f for f in all_files if f.endswith(".parquet"))
    print(f"   {len(shards)} shards. Sampling {SAMPLE_SIZE}/stratum with {WORKERS} parallel workers.\n", flush=True)

    counts: dict[str, int] = {}
    records: list[dict] = []
    lock = threading.Lock()
    stop = threading.Event()
    done_count = 0

    def process(fname: str) -> None:
        nonlocal done_count
        if stop.is_set():
            return

        df = download_and_read(fname, token)
        if df is None:
            return

        df = df.filter(
            (pl.col("file_type") == "pdf")
            & pl.col("text_content").is_not_null()
            & (pl.col("text_content").str.strip_chars().str.len_chars() > 0)
        ).with_columns(pl.col("dataset_id").cast(pl.String))

        with lock:
            done_count += 1
            added = 0
            for row in df.iter_rows(named=True):
                did = row["dataset_id"]
                if counts.get(did, 0) >= SAMPLE_SIZE:
                    continue
                records.append(row)
                counts[did] = counts.get(did, 0) + 1
                added += 1

            summary = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items())) or "—"
            print(f"[{done_count:3d}/{len(shards)}] +{added:3d}  |  {summary}", flush=True)

            if counts and all(v >= SAMPLE_SIZE for v in counts.values()):
                print(f"\n✅ All strata full — stopping.", flush=True)
                stop.set()

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures: list[Future] = []
        for fname in shards:
            if stop.is_set():
                break
            futures.append(pool.submit(process, fname))

        for f in futures:
            if stop.is_set():
                f.cancel()
            else:
                try:
                    f.result()
                except Exception as exc:
                    print(f"   ⚠️  {exc}", flush=True)

    for did, cnt in sorted(counts.items()):
        if cnt < SAMPLE_SIZE:
            print(f"⚠️  Stratum '{did}': only {cnt} docs (target {SAMPLE_SIZE}).", flush=True)

    if not records:
        print("❌ No records collected.", flush=True)
        sys.exit(1)

    print(f"\n💾 Writing {len(records):,} rows → {SAMPLE_PATH}", flush=True)
    pl.DataFrame(records).write_parquet(SAMPLE_PATH)
    print(f"✅ Done. Strata: {dict(sorted(counts.items()))}", flush=True)


if __name__ == "__main__":
    main()
