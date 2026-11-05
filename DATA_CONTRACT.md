# Data Contract v2

Single source of truth for file names, column names, types, and definitions. If something here needs to change, tell the whole team first, update this file, and bump the version at the bottom. A silent change to a column name breaks other people's code.

## 1\. Datasets

| ID | Dataset | NYC Open Data ID | Size (approx.) |
| :---- | :---- | :---- | :---- |
| H5 | DOB NOW: Build Job Application Filings | `w9ak-ipjd` | about 978k rows, 95 columns |
| T4 | Serious Injury Response, Tracking & Analysis Program (SIRTA) | `xeqp-qz8h` | about 13.3k usable rows, 23 columns |

Notes on the data:

- SIRTA contains only the serious crashes analyzed by the DOT. It is not all police-reported crashes.  
- H5 filings are paperwork, not confirmed construction.

## 2\. Windows

- Year-level analysis: complete years **2022 to 2025**.  
- Monthly series: **2022-01 to 2026-06** (where SIRTA ends).  
- H5 is loaded with `filing_date` between 2022-01-01 and 2026-06-30.

## 3\. Integration grains

Two integrated tables, both built from the same cleaned row-level files:

| Grain | Window | Used for |
| :---- | :---- | :---- |
| `zip` by `year` | 2022 to 2025 | maps, scatters, ranking and outlier questions, model |
| `borough` by `year_month` | 2022-01 to 2026-06 | seasonality, lags, time series |

Why not ZIP by month: SIRTA has too few crashes (about 1 to 2 per ZIP-month), so monthly ZIP counts are mostly zeros.

## 4\. Files

| File | Owner | Grain | Location |
| :---- | :---- | :---- | :---- |
| `housing_clean.csv` | M1 | one row per job (deduped) | `data/clean/` |
| `housing_sites_points.csv` | M1 | New Building and Full Demolition jobs with coordinates | `data/clean/` |
| `crash_clean.csv` | M2 | one row per crash | `data/clean/` |
| `nyc_zip_boundaries.geojson` | M3 | ZIP polygons (shared by everyone) | `data/clean/` |
| `zip_year_integrated.csv` | M3 | ZIP by year | `data/clean/` |
| `borough_month_integrated.csv` | M3 | borough by month (5 boroughs x 54 months \= 270 rows) | `data/clean/` |
| `coverage_report.csv` | M3 | cleaning and join coverage numbers | `data/clean/` |

Raw downloads go in `data/raw/` and are never committed.

## 5\. Keys (same names and types in every file)

| Column | Type | Rule |
| :---- | :---- | :---- |
| `zip` | string | 5 digits, zero-padded |
| `borough` | string | one of: Bronx, Brooklyn, Manhattan, Queens, Staten Island |
| `year` | int |  |
| `month` | int | 1 to 12 |
| `year_month` | string | `YYYY-MM` |

In `zip_year_integrated.csv`, each ZIP gets exactly one `borough`, taken from the boundary file or a lookup (document which).

## 6\. Housing cleaning rules (M1)

- Use H5's `postcode` as `zip`. **Never use H5's `zip` column**: it is the applicant's office address, not the property.  
- Dedupe: `job_base` is the part of `job_filing_number` before the "-". Keep one row per `job_base`. The exact rule (keep `-I1` rows, or earliest `filing_date`) is decided after the verification check in Section 11\.  
- Drop rows with a null `filing_date` (about 3k) and report the count.  
- Convert the text columns `latitude`, `longitude`, `proposed_dwelling_units`, `proposed_no_of_stories`, and `initial_cost` to numbers.  
- Set `proposed_dwelling_units` of 998 or more, and `proposed_height` of 9999999, to NaN (placeholder codes).  
- Flag IQR outliers but do not delete them (real large towers are legitimate).  
- Set coordinates outside the NYC bounding box to NaN.  
- Fill a missing `zip` from coordinates via spatial join against `nyc_zip_boundaries.geojson`, and record `zip_source`.  
- `sidewalk_shed_work_type_` and the older `shed` column appear identical: verify, then keep one.  
- Derive `days_permit_to_signoff` \= `signoff_date` minus `first_permit_date`; set to NaN if negative.

### Required columns in `housing_clean.csv`

`job_base`, `job_filing_number`, `filing_date`, `job_type`, `borough`, `zip`, `zip_source`, `latitude`, `longitude`, `proposed_dwelling_units`, `proposed_no_of_stories`, `initial_cost`, `first_permit_date`, `signoff_date`, `days_permit_to_signoff`, `is_sidewalk_shed`, `is_curb_cut`, `year`, `month`, `year_month`

### Required columns in `housing_sites_points.csv`

`job_base`, `job_type`, `borough`, `zip`, `latitude`, `longitude`, `proposed_dwelling_units`, `year`

## 7\. Crash cleaning rules (M2)

- Drop rows with a null `open_data_crash_id` or `crash_date` (about 444).  
- Dedupe on `open_data_crash_id`.  
- Standardize `crash_time` to `HH:MM`; derive `crash_hour` and `crash_weekday`.  
- Clean `zipcode` to 5 digits and name it `zip`. If missing but coordinates exist, assign the ZIP by spatial join, and record `zip_source` as `original`, `spatial_join`, or `missing`.  
- Fill a missing borough the same way, with a `borough_source` column.  
- Derive `is_highway` (a highway reference marker is present) and `is_repeat_location` (`similar_fatalities_severe` of at least 1; NaN stays NaN, not 0).  
- Set coordinates outside the NYC bounding box to NaN.

### Required columns in `crash_clean.csv`

`open_data_crash_id`, `crash_date`, `crash_time`, `crash_hour`, `crash_weekday`, `borough`, `borough_source`, `zip`, `zip_source`, `latitude`, `longitude`, `total_severe_injuries`, `total_non_severe_injuries`, `total_fatalities`, `similar_fatalities_severe`, `is_highway`, `is_repeat_location`, `year`, `month`, `year_month`

## 8\. Metrics in the integrated tables

| Column | Definition |
| :---- | :---- |
| `h_filings_total` | all deduped jobs |
| `h_new_building` | `job_type` \= New Building |
| `h_demolition` | `job_type` \= Full Demolition |
| `h_alteration_co` | `job_type` \= Alteration CO |
| `h_proposed_units` | sum of cleaned proposed dwelling units, New Building jobs only |
| `h_sidewalk_shed` | jobs with the sidewalk shed work type \= YES |
| `h_curb_cut` | jobs with the curb cut work type \= YES |
| `h_median_days_permit_to_signoff` | median of `days_permit_to_signoff` for New Building jobs (ZIP by year table only; NaN allowed) |
| `t_crashes` | serious crash count |
| `t_crashes_street` | crashes where `is_highway` is false (proposed default outcome for ZIP-level questions) |
| `t_severe_injuries` | sum of `total_severe_injuries` |
| `t_non_severe_injuries` | sum of `total_non_severe_injuries` |
| `t_fatalities` | sum of `total_fatalities` |
| `t_fatal_crashes` | crashes with at least 1 fatality |
| `t_repeat_location_crashes` | crashes where `is_repeat_location` is true |
| `t_highway_crashes` | crashes where `is_highway` is true |

Column order in `zip_year_integrated.csv`: `zip`, `borough`, `year`, then all `h_` metrics, then all `t_` metrics. Column order in `borough_month_integrated.csv`: `borough`, `year`, `month`, `year_month`, then the same metrics without `h_median_days_permit_to_signoff`.

## 9\. Post-integration rules (M3)

- Build a complete grid (every ZIP x 2022 to 2025, and every borough x 54 months) and left-join both sides onto it.  
- Fill missing **counts** with 0\. Leave medians and ratios as NaN.  
- Assert: no duplicate keys, no null keys, exact column names and types as above.  
- Write the % of crashes by `zip_source` and the number of rows dropped on each side into `coverage_report.csv`.  
- Do **not** add derived rates or lags to the shared tables. Each member computes them inside their own chart function.

## 10\. Website filters

- Housing dropdown: selects an `h_` column.  
- Transport dropdown: selects a `t_` column.  
- Borough and Year dropdowns filter the rows.  
- Search mode recognizes borough names, years 2022 to 2026, job-type words (new building, demolition, alteration), and severity words (fatal, severe).  
- All charts are functions in `src/charts/qNN.py` of the form `make_fig(df) -> plotly Figure`, taking a dataframe already filtered by the shared filter in `src/filters.py`.

## 11. Open items (verify, then update this file)

- [ ] Dedupe rule for H5 job filing numbers (check the suffix pattern such as `-I1`, and whether repeats are true duplicates).
- [x] Crash fill rates on the downloaded data. Verified: 13,309 usable rows after dropping 444 empty rows and 1 duplicate; ZIP present 60.7%, recoverable from coordinates 30.7%, unrecoverable 8.6%; borough present for 99.6%.
- [ ] Spatial-join agreement with the original ZIP (target: at least 95%), tested on crashes that have both a ZIP and coordinates. Needs the boundary file.
- [ ] Which ZIP boundary file we use, and that its ZIP field matches most H5 `postcode` values.
- [x] Exact H5 column names for the sidewalk shed and curb cut work types (verified: `sidewalk_shed_work_type_`, `shed`, `curb_cut`).
- [ ] M1: does "No Work" (11,343 rows in the raw download) count in `h_filings_total`? Proposed: no.
- [ ] M1: does "ALT-CO - New Building with Existing Elements to Remain" (14,412 rows in the raw download) count as new building? Proposed: no. Keep `h_new_building` strictly "New Building" and note the rest as a limitation.

## 12. Proposed changes (agree by [day, time], then rename this heading to "Agreed changes")

- D1: add the metric `t_crashes_street` (crashes where `is_highway` is false) to both integrated tables. Use it as the default outcome for ZIP-level construction questions. `t_crashes` stays as the total.
- D2: `coverage_report.csv` reports the share of crashes by `zip_source`, broken down by year, borough, `is_highway`, and fatal vs non-fatal.
- D3: Q3 (fatal share) uses crashes that have a ZIP only, states the coverage gap in its caption, and adds a borough-level check.
- D4: Q1 and Q7 show per-year location coverage next to the chart and include a check without 2025.
- Clarification: `zip_year_integrated.csv` counts only crashes with a ZIP (original or recovered). Crashes with no ZIP appear only in `borough_month_integrated.csv`.

### Findings behind these proposals (from the downloaded data)

- The original ZIP was filled for only 16% of 2022 crashes, versus 68 to 80% in 2023 to 2026. Without the spatial join, 2022 would look artificially quiet.
- After recovery, the share of crashes with a usable location is about 90% in 2022 and 2023, 88% in 2024, 97% in 2025, and 95% in 2026. Year-over-year ZIP changes can partly reflect coverage.
- Crashes with no location are not random: about 31% involved a fatality, versus about 5% of the rest.
- Highway crashes almost never have a ZIP (0.3%); 79% are recoverable from coordinates and 21% are unlocatable.

## Version history

- v2: SIRTA (`xeqp-qz8h`) is the crash dataset; two grains (ZIP by year, borough by month); crash metrics redefined around SIRTA columns.
- v2.1 (proposed): crash-data findings, t_crashes_street, coverage breakdowns, open decisions for H5 job types.