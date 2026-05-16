"""
01_sample.py — Build a stratified sample from the Epstein Files parquet shards.

Downloads each shard via the authenticated HuggingFace hub client (hf_hub_download),
reads it locally with polars, deletes it, and moves on. This avoids unauthenticated
direct-URL requests that trigger 429s even when a token is set.

Downloaded shards land in eda/cache/_shards/ and are deleted immediately after reading.
The final sample is written to eda/cache/sample.parquet.

Usage:
    uv run python eda/01_sample.py
"""

import os
import sys
import time
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

# Only fetch these columns — skips audio/image/video binary blobs entirely.
COLUMNS = ["dataset_id", "doc_id", "file_name", "file_type", "online_url", "text_content", "metadata"]

SHARD_DIR = CACHE_DIR / "_shards"


def download_and_read(fname: str, token: str | None, attempt: int = 0) -> pl.DataFrame | None:
    """Download a shard via authenticated HF hub, read with polars, then delete it."""
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
        Path(local_path).unlink(missing_ok=True)  # delete shard after reading
        return df
    except Exception as exc:
        if attempt >= HF_MAX_RETRIES - 1:
            print(f"   ❌ Failed after {HF_MAX_RETRIES} attempts: {exc}", flush=True)
            return None
        wait = 2 ** attempt
        print(f"   ⚠️  Retrying in {wait}s … ({exc})", flush=True)
        time.sleep(wait)
        return download_and_read(fname, token, attempt + 1)


def main() -> None:
    token = os.environ.get("HF_TOKEN") or None
    print(f"{'🔑 Using HF token.' if token else '🌐 No HF_TOKEN — anonymous (expect rate limits).'}", flush=True)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📋 Listing shards in {DATASET_NAME} …", flush=True)
    api = HfApi(token=token)
    all_files = list(api.list_repo_files(DATASET_NAME, repo_type="dataset"))
    parquet_files = sorted(f for f in all_files if f.endswith(".parquet"))
    print(f"   Found {len(parquet_files)} parquet shards.\n", flush=True)

    counts: dict[str, int] = {}
    records: list[dict] = []

    for idx, fname in enumerate(parquet_files, 1):
        summary = "  ".join(f"id={k}:{v}" for k, v in sorted(counts.items())) or "none yet"
        print(f"[{idx:3d}/{len(parquet_files)}] {fname}  |  {summary}", flush=True)

        df = download_and_read(fname, token)
        if df is None:
            continue

        df = df.filter(
            (pl.col("file_type") == "pdf")
            & pl.col("text_content").is_not_null()
            & (pl.col("text_content").str.strip_chars().str.len_chars() > 0)
        )

        if df.is_empty():
            continue

        df = df.with_columns(pl.col("dataset_id").cast(pl.String))

        for row in df.iter_rows(named=True):
            did = row["dataset_id"]
            if counts.get(did, 0) >= SAMPLE_SIZE:
                continue
            records.append(row)
            counts[did] = counts.get(did, 0) + 1

        # Stop early once all strata are full (after scanning enough files to surface rare ones).
        if idx >= 20 and all(v >= SAMPLE_SIZE for v in counts.values()):
            print(f"\n✅ All {len(counts)} strata full — stopping at shard {idx}.", flush=True)
            break

    for did, cnt in sorted(counts.items()):
        if cnt < SAMPLE_SIZE:
            print(f"⚠️  Stratum '{did}': only {cnt} qualifying docs (target {SAMPLE_SIZE}).", flush=True)

    if not records:
        print("❌ No records collected.", flush=True)
        sys.exit(1)

    print(f"\n💾 Writing {len(records):,} rows → {SAMPLE_PATH}", flush=True)
    pl.DataFrame(records).write_parquet(SAMPLE_PATH)
    print(f"✅ Done. Strata: {dict(sorted(counts.items()))}", flush=True)


if __name__ == "__main__":
    main()
