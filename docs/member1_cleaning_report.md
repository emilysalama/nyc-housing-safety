# Member 1 — DOB NOW Housing Dataset Cleaning Report

## Dataset
NYC DOB NOW: Build Job Application Filings  
Dataset ID: `w9ak-ipjd`

Original dataset: 977,813 rows and 95 columns.

Analysis date window: **2022-01-01 to 2026-06-30 (inclusive).**

## Cleaning steps
- Removed 2,957 records with missing `filing_date`.
- Restricted records to the analysis date window, resulting in 677,163 rows before deduplication.
- Created `job_base` from the part of `job_filing_number` before the first hyphen.
- Extracted `job_suffix` from `job_filing_number`.
- Deduplicated by `job_base`, retaining the earliest `filing_date`; when dates were tied, the `I1` suffix was preferred.
- Converted numeric and date columns to appropriate data types.
- Replaced placeholder values in `proposed_dwelling_units` (values >= 998) and `proposed_height` (9999999) with missing values.
- Flagged IQR outliers without deleting them.
- Validated coordinates using the NYC bounding box and set invalid or out-of-bounds coordinates to missing.
- Standardized property ZIP codes using the first five digits of `postcode`, preserving leading zeros.
- **Never used the original H5 `zip` column**, because it represents the applicant's office ZIP rather than the property's ZIP.
- Attempted to fill missing ZIP codes using spatial matching with NYC ZIP boundaries.
- Added `zip_source` to distinguish `original`, `spatial_join`, and `missing` ZIP values.
- Standardized borough names.
- Derived `year`, `month`, and `year_month`.
- Calculated `days_permit_to_signoff` and replaced negative durations with missing values.
- Created Boolean fields `is_sidewalk_shed` and `is_curb_cut`.
- Verified `shed` and `sidewalk_shed_work_type_` were identical; the redundant `shed` field was not included in the final output.

## Decisions
- `No Work` is excluded from `h_filings_total`, but records are retained.
- ALT-CO New Building with Existing Elements to Remain is excluded from strict `h_new_building`, but records are retained.
- Deduplication uses the earliest `filing_date` per `job_base`; ties prefer `I1`.
- Outliers are flagged, not removed.
- Records with unresolved missing ZIP values are retained rather than assigned unsupported ZIP codes.
- All 2,039 original records with missing `postcode` also had missing or invalid coordinates, so spatial matching could not recover their ZIP codes.

## Final cleaning results

| Measure | Result |
|---|---:|
| Original records | 977,813 |
| Records removed for missing filing date | 2,957 |
| Records within date window, before deduplication | 677,163 |
| Records removed by deduplication | 296,021 |
| Final unique jobs | 381,142 |
| Duplicate `job_base` values | 0 |
| New Building before deduplication | 49,182 |
| New Building after deduplication | 8,852 |
| `h_filings_total` (excluding No Work) | 371,264 |
| Strict `h_new_building` | 8,852 |

### Final ZIP results

| ZIP source | Rows |
|---|---:|
| Original `postcode` | 380,732 |
| Spatial join | 0 |
| Missing | 410 |
| **Total** | **381,142** |

All 380,732 non-missing ZIP values match the standardized property postcode (100% agreement).

### Site-points results

| Job type | Rows |
|---|---:|
| New Building | 8,519 |
| Full Demolition | 4,809 |
| **Total** | **13,328** |

All site-point records have valid coordinates.

## Outputs
- `housing_clean.csv` — full cleaned dataset (381,142 rows, 24 columns; 68.10 MB).
- `housing_clean_sample_5000.csv` — reproducible 5,000-row sample, generated with random seed 42.
- `housing_sites_points.csv` — 13,328 New Building and Full Demolition records with valid coordinates.
- Colab notebook containing the cleaning process.

## Storage
The full `housing_clean.csv` file is approximately **68.10 MB**, exceeding the team's approximate 50 MB GitHub guideline, so it should be shared separately through Google Drive.

The smaller `housing_sites_points.csv` and `housing_clean_sample_5000.csv` files can be committed under `data/clean/` in GitHub.

## Validation
- Final housing dataset: 381,142 rows and 24 columns.
- Zero duplicate `job_base` values.
- Date range: 2022-01-01 to 2026-06-30.
- All non-missing ZIPs are valid five-digit strings.
- ZIP/postcode agreement: 100%.
- Boolean indicator fields have Boolean data types.
- Three IQR outlier flags are present.
- Site-points dataset has zero missing coordinates.
- Sample contains exactly 5,000 rows.

**Milestone 1 — Member 1: Housing dataset cleaning and site-points preparation completed and validated.**
