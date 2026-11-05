# Member 1 — DOB NOW Housing Dataset Cleaning Report

## Dataset
NYC DOB NOW: Build Job Application Filings  
Dataset ID: `w9ak-ipjd`

## Cleaning steps
- Removed records with missing `filing_date`.
- Created `job_base` from `job_filing_number`.
- Deduplicated by `job_base`, retaining the earliest filing date.
- Converted numeric and date columns to appropriate data types.
- Replaced placeholder values in `proposed_dwelling_units` and `proposed_height` with missing values.
- Flagged IQR outliers without deleting them.
- Validated coordinates using the NYC bounding box.
- Standardized ZIP codes to five-character strings.
- Filled missing ZIP codes using spatial matching with NYC ZIP boundaries.
- Standardized borough names.
- Derived `year`, `month`, and `year_month`.
- Calculated `days_permit_to_signoff` and replaced negative durations with missing values.
- Verified `shed` and `sidewalk_shed_work_type_` were identical and dropped `shed`.

## Decisions
- `No Work` is excluded from `h_filings_total`, but records are retained.
- ALT-CO New Building with Existing Elements to Remain is excluded from strict `h_new_building`, but records are retained.
- Deduplication uses the earliest `filing_date` per `job_base`.

## Outputs
- `housing_clean.csv` — full cleaned dataset
- `housing_clean_sample.csv` — 5,000-row sample
- `housing_sites_points.csv` — New Building and Full Demolition records with valid coordinates
- Colab notebook containing the cleaning process

## Notes
Outliers and records with unresolved missing values were retained where appropriate. The full cleaned dataset is approximately 511 MB and is shared separately because of GitHub's file size limitations.
