"""Shared data loaders for the NYC housing and street safety project.

Everyone downloads data through this module, so the whole team works from the
same filtered raw files (see DATA_CONTRACT.md, sections 1 and 2).

Usage from a notebook (run from the repo root or from notebooks/):

    from src.load_data import load_housing, load_crashes
    df_housing_raw = load_housing()
    df_crash_raw = load_crashes()

Usage from the terminal (repo root):

    python -m src.load_data            # download both datasets and cache them
    python -m src.load_data --check    # only check that the column names exist
    python -m src.load_data --refresh  # ignore the cache and download again

Downloads are cached as CSV files in data/raw/ (this folder is git-ignored).
Set the environment variable SOCRATA_APP_TOKEN to get higher API rate limits
(optional).
"""
from __future__ import annotations

import io
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
# Use the operating system's certificate store for HTTPS. This fixes
# "CERTIFICATE_VERIFY_FAILED" errors on some Windows machines and networks.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
CLEAN_DIR = REPO_ROOT / "data" / "clean"

# ---------------------------------------------------------------------------
# Datasets (NYC Open Data)
# ---------------------------------------------------------------------------
H5_ID = "w9ak-ipjd"  # DOB NOW: Build - Job Application Filings
T4_ID = "xeqp-qz8h"  # Serious Injury Response, Tracking & Analysis Program (SIRTA)
API_URL = "https://data.cityofnewyork.us/resource/{}.csv"

# Window agreed in DATA_CONTRACT.md (SIRTA ends 2026-06-30)
START_DATE = "2022-01-01"
END_DATE = "2026-06-30"

# H5 has about 978k rows and 95 columns. We only download the columns the
# contract needs, and only the rows inside the window, so the notebook and the
# free-tier deployment do not run out of memory.
# If you need another column, add it here and tell the team.
H5_COLS = [
    "job_filing_number",
    "filing_date",
    "filing_status",
    "job_type",
    "borough",
    "postcode",  # PROPERTY zip. Do NOT use H5's "zip" column (applicant's office).
    "latitude",
    "longitude",
    "proposed_dwelling_units",
    "proposed_no_of_stories",
    "proposed_height",
    "initial_cost",
    "first_permit_date",
    "signoff_date",
    "sidewalk_shed_work_type_",
    "shed",
    "curb_cut",
    "building_type",
    "owner_type",
    "bbl",
]

PAGE_SIZE = 50_000  # rows per request; we page with $offset until the end

# Keep ZIP codes as text so leading zeros and formats are not mangled.
STR_COLS = {"postcode": str, "zipcode": str}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def _fetch_csv(dataset_id: str, params: dict, retries: int = 3) -> pd.DataFrame:
    """Download one page of a dataset as a DataFrame, with simple retries."""
    url = API_URL.format(dataset_id) + "?" + urlencode(params)
    headers = {}
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token

    for attempt in range(1, retries + 1):
        try:
            with urlopen(Request(url, headers=headers), timeout=120) as response:
                text = response.read().decode("utf-8")
            if not text.strip():
                return pd.DataFrame()
            return pd.read_csv(io.StringIO(text), dtype=STR_COLS, low_memory=False)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        except HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")[:500]
            # 4xx means our request is wrong (for example a misspelled column):
            # retrying will not help, so fail with the server's explanation.
            if err.code < 500:
                raise RuntimeError(f"HTTP {err.code} from {dataset_id}: {body}") from err
            if attempt == retries:
                raise
        except Exception as err:  # network hiccup, timeout, ...
            if attempt == retries:
                raise
            print(f"  attempt {attempt} failed ({err}); retrying...")
        time.sleep(2 * attempt)
    return pd.DataFrame()  # unreachable, keeps type checkers happy


def _download_all(dataset_id: str, params: dict) -> pd.DataFrame:
    """Download every page of a query (the API caps rows per request)."""
    pages, offset = [], 0
    while True:
        page_params = {**params, "$limit": PAGE_SIZE, "$offset": offset, "$order": ":id"}
        page = _fetch_csv(dataset_id, page_params)
        pages.append(page)
        print(f"  fetched {offset + len(page):,} rows")
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    non_empty = [p for p in pages if not p.empty]
    return pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame()


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------
def load_housing(refresh: bool = False, start: str = START_DATE, end: str = END_DATE) -> pd.DataFrame:
    """H5 filings between `start` and `end` (filing_date), selected columns only."""
    cache = RAW_DIR / f"h5_{start}_{end}.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache, dtype=STR_COLS, low_memory=False)

    print(f"Downloading H5 ({H5_ID}) filings {start} to {end} ...")
    params = {
        "$select": ",".join(H5_COLS),
        "$where": f"filing_date >= '{start}T00:00:00' AND filing_date <= '{end}T23:59:59'",
    }
    df = _download_all(H5_ID, params)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False)
    return df


def load_crashes(refresh: bool = False) -> pd.DataFrame:
    """All SIRTA rows (small dataset, all 23 columns)."""
    cache = RAW_DIR / "t4_sirta.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache, dtype=STR_COLS, low_memory=False)

    print(f"Downloading SIRTA ({T4_ID}) ...")
    df = _download_all(T4_ID, {})
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False)
    return df


# ---------------------------------------------------------------------------
# Column check: run this first, before the big download
# ---------------------------------------------------------------------------
def check_columns() -> None:
    """Fetch one row of each dataset and report any column names that do not exist."""
    h5 = _fetch_csv(H5_ID, {"$limit": 1})
    missing = [c for c in H5_COLS if c not in h5.columns]
    print(f"H5: {len(h5.columns)} columns available.")
    print("  missing from H5_COLS:", missing if missing else "none (all names are valid)")

    t4 = _fetch_csv(T4_ID, {"$limit": 1})
    print(f"SIRTA: {len(t4.columns)} columns available:")
    print("  ", list(t4.columns))


if __name__ == "__main__":
    if "--check" in sys.argv:
        check_columns()
    else:
        refresh_flag = "--refresh" in sys.argv
        housing = load_housing(refresh=refresh_flag)
        crashes = load_crashes(refresh=refresh_flag)
        print(f"H5 housing: {housing.shape[0]:,} rows x {housing.shape[1]} columns")
        print(f"SIRTA crashes: {crashes.shape[0]:,} rows x {crashes.shape[1]} columns")
