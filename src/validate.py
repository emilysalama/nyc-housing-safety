"""Check a cleaned or integrated file against DATA_CONTRACT.md.

Run from the repo root:

    python -m src.validate housing        data/clean/housing_clean.csv
    python -m src.validate crash          data/clean/crash_clean.csv
    python -m src.validate zip_year       data/clean/zip_year_integrated.csv
    python -m src.validate borough_month  data/clean/borough_month_integrated.csv

Every check prints PASS, FAIL, or WARN. FAIL means the file breaks the contract and
must be fixed before the handoff. WARN means "look at this". The exit code is 1 if
any check fails.

Keep the column lists below in sync with DATA_CONTRACT.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

WINDOW_START, WINDOW_END = "2022-01-01", "2026-06-30"
YEARS = [2022, 2023, 2024, 2025]
BOROUGHS = {"Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"}
ZIP_SOURCES = {"original", "spatial_join", "missing"}
NYC_LAT, NYC_LON = (40.4, 41.0), (-74.3, -73.6)  # rough NYC bounding box
NYC_ZIP_MIN, NYC_ZIP_MAX = "10001", "11697"
JOB_TYPES = {"Alteration", "New Building", "Alteration CO", "No Work", "Full Demolition",
             "ALT-CO - New Building with Existing Elements to Remain"}

HOUSING_REQUIRED = [
    "job_base", "job_filing_number", "filing_date", "job_type", "borough", "zip", "zip_source",
    "latitude", "longitude", "proposed_dwelling_units", "proposed_no_of_stories", "initial_cost",
    "first_permit_date", "signoff_date", "days_permit_to_signoff", "is_sidewalk_shed",
    "is_curb_cut", "year", "month", "year_month",
]
CRASH_REQUIRED = [
    "open_data_crash_id", "crash_date", "crash_time", "crash_hour", "crash_weekday", "borough",
    "borough_source", "zip", "zip_source", "latitude", "longitude", "total_severe_injuries",
    "total_non_severe_injuries", "total_fatalities", "similar_fatalities_severe", "is_highway",
    "is_repeat_location", "year", "month", "year_month",
]
H_METRICS = ["h_filings_total", "h_new_building", "h_demolition", "h_alteration_co",
             "h_proposed_units", "h_sidewalk_shed", "h_curb_cut"]
T_METRICS = ["t_crashes", "t_crashes_street", "t_severe_injuries", "t_non_severe_injuries",
             "t_fatalities", "t_fatal_crashes", "t_repeat_location_crashes", "t_highway_crashes"]
ZIP_YEAR_COLS = (["zip", "borough", "year"] + H_METRICS
                 + ["h_median_days_permit_to_signoff"] + T_METRICS)
BOROUGH_MONTH_COLS = ["borough", "year", "month", "year_month"] + H_METRICS + T_METRICS


class Report:
    """Collects PASS / FAIL / WARN lines and prints them."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.rows.append(("PASS" if ok else "FAIL", label, "" if ok else detail))
        return bool(ok)

    def warn_if(self, bad: bool, label: str, detail: str = "") -> None:
        self.rows.append(("WARN" if bad else "PASS", label, detail if bad else ""))

    def show(self, title: str) -> int:
        print(f"\n{title}\n" + "-" * len(title))
        for status, label, detail in self.rows:
            print(f"{status:<5} {label}" + (f"  ->  {detail}" if detail else ""))
        fails = sum(1 for s, _, _ in self.rows if s == "FAIL")
        warns = sum(1 for s, _, _ in self.rows if s == "WARN")
        print(f"\n{fails} failed, {warns} warnings, {len(self.rows) - fails - warns} passed")
        return fails


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates that may mix formats (with and without a time part)."""
    try:
        return pd.to_datetime(series, format="mixed", errors="coerce")
    except (TypeError, ValueError):  # older pandas without format="mixed"
        return pd.to_datetime(series, errors="coerce")


def _require_columns(r: Report, df: pd.DataFrame, needed: list[str]) -> pd.DataFrame:
    """Report missing required columns, then pad them with NaN so the other checks
    still run (a missing column must not hide a wrong ZIP or a wrong date window)."""
    missing = [c for c in needed if c not in df.columns]
    r.check(not missing, "required columns present", f"missing: {missing}")
    return df.reindex(columns=list(df.columns) + missing) if missing else df


def _check_zip(r: Report, df: pd.DataFrame) -> None:
    z = df["zip"]
    present = z.notna()
    bad_format = present & ~z.astype(str).str.fullmatch(r"\d{5}")
    r.check(bad_format.sum() == 0, "zip values are exactly 5 digits",
            f"{int(bad_format.sum())} values are not 5 digits, e.g. {z[bad_format].head(3).tolist()}")
    outside = present & ~z.astype(str).str[:5].between(NYC_ZIP_MIN, NYC_ZIP_MAX)
    r.check(outside.mean() < 0.005, "zip values are NYC ZIPs",
            f"{int(outside.sum())} of {len(df)} zips ({outside.mean():.1%}) are outside the NYC range")
    r.warn_if(z.isna().mean() > 0.01, "zip missing share is small", f"{z.isna().mean():.1%} missing")
    if "zip_source" in df.columns:
        values = set(df["zip_source"].dropna().unique())
        r.check(values <= ZIP_SOURCES, "zip_source values are original / spatial_join / missing",
                f"unexpected values: {sorted(values - ZIP_SOURCES)}")


def _check_coords(r: Report, df: pd.DataFrame) -> None:
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    bad = (lat.notna() & ~lat.between(*NYC_LAT)) | (lon.notna() & ~lon.between(*NYC_LON))
    r.check(bad.sum() == 0, "coordinates are inside the NYC bounding box", f"{int(bad.sum())} outside")


def _check_window(r: Report, dates: pd.Series) -> None:
    r.check(dates.notna().all(), "dates parse", f"{int(dates.isna().sum())} unparseable or missing")
    start, end = pd.Timestamp(WINDOW_START), pd.Timestamp(WINDOW_END) + pd.Timedelta(days=1)
    outside = dates.notna() & ((dates < start) | (dates >= end))
    r.check(outside.sum() == 0, f"dates inside {WINDOW_START} to {WINDOW_END}",
            f"{int(outside.sum())} of {len(dates)} rows outside the window "
            f"(range {dates.min()} to {dates.max()})")


def _check_date_parts(r: Report, df: pd.DataFrame, dates: pd.Series) -> None:
    ok = ((dates.dt.year == pd.to_numeric(df["year"], errors="coerce"))
          & (dates.dt.month == pd.to_numeric(df["month"], errors="coerce"))
          & (dates.dt.strftime("%Y-%m") == df["year_month"].astype(str)))
    r.check(ok.all(), "year, month, year_month match the date", f"{int((~ok).sum())} rows disagree")


def _check_boolean_like(r: Report, df: pd.DataFrame, col: str) -> None:
    values = df[col].dropna().astype(str).str.lower()
    r.check(values.isin(["true", "false", "1", "0"]).all(), f"{col} is true/false",
            f"unexpected values: {sorted(set(values) - {'true', 'false', '1', '0'})[:5]}")


def validate_housing(df: pd.DataFrame, r: Report) -> None:
    df = _require_columns(r, df, HOUSING_REQUIRED)
    extra = [c for c in df.columns if c not in HOUSING_REQUIRED]
    r.warn_if(len(extra) > 12, "no big pile of extra columns",
              f"{len(extra)} extra columns; keep only what the contract needs (smaller file, no personal names)")
    _check_zip(r, df)
    if "postcode" in df.columns:  # catches the applicant-ZIP mistake
        both = df["zip"].notna() & df["postcode"].notna() & df["postcode"].astype(str).str.fullmatch(r"\d{5}.*")
        same = (df.loc[both, "zip"].astype(str).str[:5] == df.loc[both, "postcode"].astype(str).str[:5]).mean()
        r.check(same >= 0.99, "zip comes from the property postcode (not the applicant's zip)",
                f"zip equals postcode on only {same:.1%} of rows")
    r.check(df["borough"].dropna().isin(BOROUGHS).all() and df["borough"].notna().all(),
            "borough is one of the 5 standard names")
    dates = _parse_dates(df["filing_date"])
    _check_window(r, dates)
    _check_date_parts(r, df, dates)
    r.check(not df["job_base"].duplicated().any(), "one row per job_base",
            f"{int(df['job_base'].duplicated().sum())} duplicates")
    unexpected = set(df["job_type"].dropna().unique()) - JOB_TYPES
    r.warn_if(bool(unexpected), "job_type values are the known six", f"unexpected: {sorted(unexpected)}")
    _check_boolean_like(r, df, "is_sidewalk_shed")
    _check_boolean_like(r, df, "is_curb_cut")
    days = pd.to_numeric(df["days_permit_to_signoff"], errors="coerce")
    r.check((days.dropna() >= 0).all(), "days_permit_to_signoff has no negatives",
            f"{int((days < 0).sum())} negative")
    _check_coords(r, df)


def validate_crash(df: pd.DataFrame, r: Report) -> None:
    df = _require_columns(r, df, CRASH_REQUIRED)
    r.check(df["open_data_crash_id"].notna().all() and df["crash_date"].notna().all(),
            "no null crash id or date")
    r.check(not df["open_data_crash_id"].duplicated().any(), "one row per crash id",
            f"{int(df['open_data_crash_id'].duplicated().sum())} duplicates")
    _check_zip(r, df)
    unexpected = df["borough"].notna() & ~df["borough"].isin(BOROUGHS)
    r.check(not unexpected.any(), "borough values are the 5 standard names",
            f"{int(unexpected.sum())} unexpected values, e.g. {df.loc[unexpected, 'borough'].head(3).tolist()}")
    missing = df["borough"].isna()
    fillable = missing & df["latitude"].notna() & df["longitude"].notna()
    r.check(not fillable.any(), "no missing borough that coordinates could fill",
            f"{int(fillable.sum())} rows have coordinates but no borough (fill by spatial join, set borough_source)")
    r.warn_if(missing.any(), "borough missing share is small",
              f"{int(missing.sum())} missing ({missing.mean():.1%}); report in coverage_report.csv")
    dates = _parse_dates(df["crash_date"])
    _check_window(r, dates)
    _check_date_parts(r, df, dates)
    r.check(df["crash_time"].astype(str).str.fullmatch(r"([01]\d|2[0-3]):[0-5]\d").all(),
            "crash_time is HH:MM")
    r.check(pd.to_numeric(df["crash_hour"], errors="coerce").between(0, 23).all(), "crash_hour is 0 to 23")
    _check_boolean_like(r, df, "is_highway")
    _check_boolean_like(r, df, "is_repeat_location")
    _check_coords(r, df)


def _check_counts(r: Report, df: pd.DataFrame) -> None:
    counts = df[H_METRICS + T_METRICS]
    r.check(counts.notna().all().all() and (counts >= 0).all().all(),
            "count columns have no NaN and no negatives (zero-filled)")
    r.check((df["t_crashes_street"] <= df["t_crashes"]).all(), "t_crashes_street <= t_crashes")
    r.check((df["t_fatal_crashes"] <= df["t_crashes"]).all(), "t_fatal_crashes <= t_crashes")
    r.check((df["h_new_building"] <= df["h_filings_total"]).all(), "h_new_building <= h_filings_total")


def validate_zip_year(df: pd.DataFrame, r: Report) -> None:
    same_cols = list(df.columns) == ZIP_YEAR_COLS
    r.check(same_cols, "columns and order match the contract",
            f"missing {[c for c in ZIP_YEAR_COLS if c not in df.columns]}, "
            f"extra {[c for c in df.columns if c not in ZIP_YEAR_COLS]}")
    if not set(ZIP_YEAR_COLS) <= set(df.columns):
        return
    r.check(not df.duplicated(["zip", "year"]).any(), "unique (zip, year) keys")
    r.check(df[["zip", "borough", "year"]].notna().all().all(), "no null keys")
    _check_zip(r, df)
    r.check(sorted(df["year"].unique()) == YEARS, "years are 2022 to 2025", f"found {sorted(df['year'].unique())}")
    r.check((df.groupby("zip")["year"].nunique() == len(YEARS)).all(), "every ZIP has all 4 years (complete grid)")
    r.check((df.groupby("zip")["borough"].nunique() == 1).all(), "each ZIP has exactly one borough")
    _check_counts(r, df)


def validate_borough_month(df: pd.DataFrame, r: Report) -> None:
    same_cols = list(df.columns) == BOROUGH_MONTH_COLS
    r.check(same_cols, "columns and order match the contract",
            f"missing {[c for c in BOROUGH_MONTH_COLS if c not in df.columns]}, "
            f"extra {[c for c in df.columns if c not in BOROUGH_MONTH_COLS]}")
    if not set(BOROUGH_MONTH_COLS) <= set(df.columns):
        return
    r.check(len(df) == 5 * 54, "270 rows (5 boroughs x 54 months)", f"{len(df)} rows")
    r.check(not df.duplicated(["borough", "year_month"]).any(), "unique (borough, year_month) keys")
    r.check(set(df["borough"]) == BOROUGHS, "the 5 standard boroughs")
    months = pd.period_range(WINDOW_START[:7], WINDOW_END[:7], freq="M").astype(str)
    r.check(set(df["year_month"]) == set(months), "year_month covers 2022-01 to 2026-06")
    _check_counts(r, df)


KINDS = {"housing": validate_housing, "crash": validate_crash,
         "zip_year": validate_zip_year, "borough_month": validate_borough_month}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in KINDS:
        print(__doc__)
        return 2
    kind, path = argv[1], Path(argv[2])
    df = pd.read_csv(path, dtype={"zip": str, "postcode": str}, low_memory=False)
    report = Report()
    KINDS[kind](df, report)
    return 1 if report.show(f"{kind}: {path.name} ({len(df):,} rows)") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
