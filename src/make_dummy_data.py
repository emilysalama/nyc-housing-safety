"""Generate SYNTHETIC data shaped exactly like DATA_CONTRACT.md.

Why: the website and the chart functions can be built and tested before the real
cleaned and integrated files exist (Friday evening handoff). Everything here is
made up. The relationships between construction and crashes are invented, so
NEVER quote a result from dummy data.

Run from the repo root:

    python -m src.make_dummy_data

It writes three files to data/dummy/ (not data/clean/, so nobody mistakes dummy
files for real ones):

    zip_year_integrated.csv       ZIP by year, 2022 to 2025
    borough_month_integrated.csv  borough by month, 2022-01 to 2026-06
    crash_clean.csv               one row per crash (row-level, for Q2, Q10, Q11)

In a notebook or the app:

    from src.make_dummy_data import load_dummy
    zip_year = load_dummy("zip_year_integrated")
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DUMMY_DIR = REPO_ROOT / "data" / "dummy"
SEED = 42

YEARS = [2022, 2023, 2024, 2025]  # complete years (DATA_CONTRACT section 2)
MONTHS = pd.period_range("2022-01", "2026-06", freq="M")  # 54 months

# Made-up ZIP list: (borough, first ZIP, how many ZIPs). Not the real ZIP list.
ZIP_BLOCKS = [
    ("Manhattan", 10001, 40),
    ("Bronx", 10451, 25),
    ("Brooklyn", 11201, 38),
    ("Queens", 11354, 45),
    ("Staten Island", 10301, 14),
]
BOROUGH_CENTER = {  # rough lat/lon centers, only used to scatter fake points
    "Manhattan": (40.78, -73.97),
    "Bronx": (40.85, -73.88),
    "Brooklyn": (40.65, -73.95),
    "Queens": (40.72, -73.80),
    "Staten Island": (40.58, -74.15),
}

# Column lists, in the exact order required by DATA_CONTRACT.md section 8
H_METRICS = [
    "h_filings_total", "h_new_building", "h_demolition", "h_alteration_co",
    "h_proposed_units", "h_sidewalk_shed", "h_curb_cut",
]
T_METRICS = [
    "t_crashes", "t_crashes_street", "t_severe_injuries", "t_non_severe_injuries",
    "t_fatalities", "t_fatal_crashes", "t_repeat_location_crashes", "t_highway_crashes",
]
ZIP_YEAR_COLS = (["zip", "borough", "year"] + H_METRICS
                 + ["h_median_days_permit_to_signoff"] + T_METRICS)
BOROUGH_MONTH_COLS = ["borough", "year", "month", "year_month"] + H_METRICS + T_METRICS
CRASH_COLS = [
    "open_data_crash_id", "crash_date", "crash_time", "crash_hour", "crash_weekday",
    "borough", "borough_source", "zip", "zip_source", "latitude", "longitude",
    "total_severe_injuries", "total_non_severe_injuries", "total_fatalities",
    "similar_fatalities_severe", "is_highway", "is_repeat_location",
    "year", "month", "year_month",
]

# Mimic the real coverage pattern we measured: ZIP was rarely filled in 2022
ORIGINAL_ZIP_SHARE = {2022: 0.16, 2023: 0.68, 2024: 0.70, 2025: 0.80, 2026: 0.74}
UNLOCATED_SHARE = {2022: 0.10, 2023: 0.10, 2024: 0.12, 2025: 0.03, 2026: 0.05}

_HOURS = np.arange(24)
_WEEKDAY_P = 1 + 2.5 * np.exp(-((_HOURS - 8) ** 2) / 6) + 3.0 * np.exp(-((_HOURS - 17.5) ** 2) / 8)
_WEEKEND_P = (1 + 1.5 * np.exp(-((_HOURS - 14) ** 2) / 18)
              + 3.0 * np.exp(-((_HOURS - 23) ** 2) / 6) + 2.0 * np.exp(-((_HOURS - 1) ** 2) / 4))
_WEEKDAY_P, _WEEKEND_P = _WEEKDAY_P / _WEEKDAY_P.sum(), _WEEKEND_P / _WEEKEND_P.sum()


def load_dummy(name: str) -> pd.DataFrame:
    """Read a dummy file by name (without .csv), keeping ZIP codes as text."""
    return pd.read_csv(DUMMY_DIR / f"{name}.csv", dtype={"zip": str})


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
def make_zip_table(rng: np.random.Generator) -> pd.DataFrame:
    """One row per fake ZIP with a hidden construction intensity and crash risk."""
    rows = [{"zip": str(start + i), "borough": borough}
            for borough, start, n in ZIP_BLOCKS for i in range(n)]
    zips = pd.DataFrame(rows)
    zips["activity"] = rng.lognormal(mean=0.0, sigma=0.8, size=len(zips))
    zips["danger"] = rng.lognormal(mean=0.0, sigma=0.5, size=len(zips))
    return zips


def make_housing_zip_month(zips: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Fake monthly housing counts per ZIP (hidden intensity drives the counts)."""
    grid = zips.merge(pd.DataFrame({"period": MONTHS}), how="cross")
    grid["year"] = grid["period"].dt.year
    grid["month"] = grid["period"].dt.month
    grid["year_month"] = grid["period"].astype(str)

    season = 1 + 0.15 * np.sin((grid["month"] - 3) / 12 * 2 * np.pi)
    a = grid["activity"] * season
    grid["h_new_building"] = rng.poisson(0.6 * a)
    grid["h_demolition"] = rng.poisson(0.1 * a)
    grid["h_alteration_co"] = rng.poisson(0.5 * a)
    grid["h_sidewalk_shed"] = rng.poisson(1.5 * a)
    grid["h_curb_cut"] = rng.poisson(0.2 * a)
    grid["h_proposed_units"] = grid["h_new_building"] * rng.integers(4, 60, size=len(grid))
    other = rng.poisson(6 * a)
    grid["h_filings_total"] = (other + grid["h_new_building"] + grid["h_demolition"]
                               + grid["h_alteration_co"] + grid["h_sidewalk_shed"]
                               + grid["h_curb_cut"])
    return grid


def make_crashes(zips: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """One row per fake crash, shaped like crash_clean.csv."""
    grid = zips.merge(pd.DataFrame({"period": MONTHS}), how="cross")
    lam = grid["danger"] * (0.6 + 0.4 * grid["activity"])  # crashes per ZIP-month
    counts = rng.poisson(lam)
    c = grid.loc[grid.index.repeat(counts)].reset_index(drop=True)
    n = len(c)

    year = c["period"].dt.year.to_numpy()
    c["year"] = year
    c["month"] = c["period"].dt.month
    c["year_month"] = c["period"].astype(str)
    days = rng.integers(0, 28, size=n)
    c["crash_date"] = c["period"].dt.start_time + pd.to_timedelta(days, unit="D")
    c["crash_weekday"] = c["crash_date"].dt.day_name()
    weekend = c["crash_date"].dt.dayofweek.to_numpy() >= 5

    hours = np.where(weekend,
                     rng.choice(24, size=n, p=_WEEKEND_P),
                     rng.choice(24, size=n, p=_WEEKDAY_P))
    c["crash_hour"] = hours
    minutes = rng.integers(0, 60, size=n)
    c["crash_time"] = [f"{h:02d}:{m:02d}" for h, m in zip(hours, minutes)]

    # ZIP source: original / spatial_join / missing, with the real year pattern
    u = rng.random(n)
    unloc = np.array([UNLOCATED_SHARE[y] for y in year])
    orig = np.array([ORIGINAL_ZIP_SHARE[y] for y in year])
    source = np.where(u < unloc, "missing",
                      np.where(u < unloc + orig, "original", "spatial_join"))
    c["zip_source"] = source
    c.loc[source == "missing", "zip"] = np.nan
    c["borough_source"] = "original"

    # Fake coordinates around each borough center (none for unlocated crashes)
    centers = c["borough"].map(BOROUGH_CENTER)
    c["latitude"] = [ctr[0] for ctr in centers] + rng.normal(0, 0.03, n)
    c["longitude"] = [ctr[1] for ctr in centers] + rng.normal(0, 0.03, n)
    no_coords = (source == "missing") | ((source == "original") & (rng.random(n) < 0.10))
    c.loc[no_coords, ["latitude", "longitude"]] = np.nan

    # Severity: unlocated crashes are more often fatal (the pattern in the real data)
    fatal = rng.random(n) < np.where(source == "missing", 0.31, 0.055)
    c["total_fatalities"] = fatal.astype(int)
    severe = np.where(fatal, rng.choice([0, 1], size=n),
                      rng.choice([1, 2, 3], size=n, p=[0.85, 0.12, 0.03]))
    c["total_severe_injuries"] = severe
    c["total_non_severe_injuries"] = rng.poisson(1.2, size=n)
    c["similar_fatalities_severe"] = rng.poisson(0.4, size=n)
    c["is_repeat_location"] = c["similar_fatalities_severe"] >= 1
    c["is_highway"] = rng.random(n) < 0.08

    c["open_data_crash_id"] = 9_000_001 + np.arange(n)
    return c[CRASH_COLS]


def _crash_flags(crashes: pd.DataFrame) -> pd.DataFrame:
    """Add the t_ columns that are summed in the integrated tables."""
    c = crashes.copy()
    c["t_crashes"] = 1
    c["t_crashes_street"] = (~c["is_highway"]).astype(int)
    c["t_severe_injuries"] = c["total_severe_injuries"]
    c["t_non_severe_injuries"] = c["total_non_severe_injuries"]
    c["t_fatalities"] = c["total_fatalities"]
    c["t_fatal_crashes"] = (c["total_fatalities"] > 0).astype(int)
    c["t_repeat_location_crashes"] = c["is_repeat_location"].astype(int)
    c["t_highway_crashes"] = c["is_highway"].astype(int)
    return c


def build_zip_year(zips, housing, crashes, rng) -> pd.DataFrame:
    """ZIP by year table. Counts only crashes that have a ZIP (contract section 12)."""
    grid = zips[["zip", "borough"]].merge(pd.DataFrame({"year": YEARS}), how="cross")
    h = housing[housing["year"].isin(YEARS)].groupby(["zip", "year"], as_index=False)[H_METRICS].sum()
    located = crashes[crashes["zip"].notna() & crashes["year"].isin(YEARS)]
    t = _crash_flags(located).groupby(["zip", "year"], as_index=False)[T_METRICS].sum()

    out = grid.merge(h, on=["zip", "year"], how="left").merge(t, on=["zip", "year"], how="left")
    out[H_METRICS + T_METRICS] = out[H_METRICS + T_METRICS].fillna(0).astype(int)  # counts: 0 not NaN
    days = np.round(np.clip(rng.normal(900, 250, size=len(out)), 120, None))
    out["h_median_days_permit_to_signoff"] = np.where(out["h_new_building"] > 0, days, np.nan)
    return out[ZIP_YEAR_COLS]


def build_borough_month(housing, crashes) -> pd.DataFrame:
    """Borough by month table. Counts ALL crashes, including those without a ZIP."""
    boroughs = [b for b, _, _ in ZIP_BLOCKS]
    grid = pd.DataFrame([(b, str(p)) for b in boroughs for p in MONTHS],
                        columns=["borough", "year_month"])
    h = housing.groupby(["borough", "year_month"], as_index=False)[H_METRICS].sum()
    t = _crash_flags(crashes).groupby(["borough", "year_month"], as_index=False)[T_METRICS].sum()

    out = grid.merge(h, on=["borough", "year_month"], how="left").merge(t, on=["borough", "year_month"], how="left")
    out[H_METRICS + T_METRICS] = out[H_METRICS + T_METRICS].fillna(0).astype(int)
    out["year"] = out["year_month"].str[:4].astype(int)
    out["month"] = out["year_month"].str[5:7].astype(int)
    return out[BOROUGH_MONTH_COLS]


def check_contract(zip_year, borough_month, crashes) -> None:
    """Small version of the contract assertions (DATA_CONTRACT section 9)."""
    assert list(zip_year.columns) == ZIP_YEAR_COLS
    assert list(borough_month.columns) == BOROUGH_MONTH_COLS
    assert list(crashes.columns) == CRASH_COLS
    assert not zip_year.duplicated(["zip", "year"]).any()
    assert not borough_month.duplicated(["borough", "year_month"]).any()
    assert zip_year[["zip", "borough", "year"]].notna().all().all()
    assert zip_year["zip"].str.len().eq(5).all()
    assert len(borough_month) == 5 * len(MONTHS)


def main() -> None:
    rng = np.random.default_rng(SEED)
    zips = make_zip_table(rng)
    housing = make_housing_zip_month(zips, rng)
    crashes = make_crashes(zips, rng)
    zip_year = build_zip_year(zips, housing, crashes, rng)
    borough_month = build_borough_month(housing, crashes)
    check_contract(zip_year, borough_month, crashes)

    DUMMY_DIR.mkdir(parents=True, exist_ok=True)
    zip_year.to_csv(DUMMY_DIR / "zip_year_integrated.csv", index=False)
    borough_month.to_csv(DUMMY_DIR / "borough_month_integrated.csv", index=False)
    crashes.to_csv(DUMMY_DIR / "crash_clean.csv", index=False)
    print("SYNTHETIC data written to", DUMMY_DIR)
    print(f"  zip_year_integrated.csv      {zip_year.shape}")
    print(f"  borough_month_integrated.csv {borough_month.shape}")
    print(f"  crash_clean.csv              {crashes.shape}")


if __name__ == "__main__":
    main()
