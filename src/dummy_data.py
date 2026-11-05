"""Generate fake integrated tables with the exact contract columns.
Writes to data/dummy/ so real files in data/clean/ are never overwritten.
Run from repo root: python -m src.dummy_data"""
import numpy as np
import pandas as pd
from pathlib import Path

BOROUGHS = ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
H_COLS = ["h_filings_total", "h_new_building", "h_demolition", "h_alteration_co",
          "h_proposed_units", "h_sidewalk_shed", "h_curb_cut"]
T_COLS = ["t_crashes", "t_crashes_street", "t_severe_injuries", "t_non_severe_injuries",
          "t_fatalities", "t_fatal_crashes", "t_repeat_location_crashes", "t_highway_crashes"]

def make_zip_year(seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(180):
        zip_code = f"{10001 + i * 5:05d}"
        borough = BOROUGHS[i % 5]
        size = rng.gamma(2, 2)
        for year in range(2022, 2026):
            h_total = rng.poisson(40 * size)
            row = {"zip": zip_code, "borough": borough, "year": year,
                   "h_filings_total": h_total,
                   "h_new_building": rng.poisson(3 * size),
                   "h_demolition": rng.poisson(0.5 * size),
                   "h_alteration_co": rng.poisson(8 * size),
                   "h_proposed_units": rng.poisson(30 * size),
                   "h_sidewalk_shed": rng.poisson(6 * size),
                   "h_curb_cut": rng.poisson(1 * size),
                   "h_median_days_permit_to_signoff": rng.normal(600, 150) if rng.random() > .2 else np.nan}
            crashes = rng.poisson(1 + size)
            hw = min(crashes, rng.poisson(0.1))
            row.update({"t_crashes": crashes, "t_crashes_street": crashes - hw,
                        "t_severe_injuries": rng.poisson(crashes * 1.1),
                        "t_non_severe_injuries": rng.poisson(crashes * 0.5),
                        "t_fatalities": rng.binomial(crashes, .1),
                        "t_fatal_crashes": rng.binomial(crashes, .09),
                        "t_repeat_location_crashes": rng.binomial(crashes, .3),
                        "t_highway_crashes": hw})
            rows.append(row)
    return pd.DataFrame(rows)

def make_borough_month(seed=43):
    rng = np.random.default_rng(seed)
    months = pd.period_range("2022-01", "2026-06", freq="M")
    rows = []
    for b in BOROUGHS:
        for p in months:
            c = rng.poisson(30)
            hw = rng.poisson(2)
            row = {"borough": b, "year": p.year, "month": p.month, "year_month": str(p)}
            for h in H_COLS:
                row[h] = rng.poisson(50)
            row.update({"t_crashes": c, "t_crashes_street": c - hw,
                        "t_severe_injuries": rng.poisson(c), "t_non_severe_injuries": rng.poisson(c / 2),
                        "t_fatalities": rng.poisson(3), "t_fatal_crashes": rng.poisson(3),
                        "t_repeat_location_crashes": rng.poisson(8), "t_highway_crashes": hw})
            rows.append(row)
    return pd.DataFrame(rows)

if __name__ == "__main__":
    out = Path("data/dummy"); out.mkdir(parents=True, exist_ok=True)
    make_zip_year().to_csv(out / "zip_year_integrated.csv", index=False)
    make_borough_month().to_csv(out / "borough_month_integrated.csv", index=False)
    print("wrote", out)
