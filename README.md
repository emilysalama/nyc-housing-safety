# NYC Housing and Street Safety

Does new housing construction go hand in hand with serious street crashes? An interactive data story built from two NYC Open Data datasets for the Data Engineering and Visualization course (GIU, Winter 2026).

- **Live website:** https://nyc-housing-safety.onrender.com/
- **Notebook:** `notebooks/master_notebook.ipynb`

## Datasets

| Domain | Dataset | Link |
|---|---|---|
| Housing and Development | DOB NOW: Build Job Application Filings (H5) | https://data.cityofnewyork.us/d/w9ak-ipjd |
| Transportation | Serious Injury Response, Tracking and Analysis Program, SIRTA (T4) | https://data.cityofnewyork.us/d/xeqp-qz8h |

How the two are integrated, the file names, and the column definitions are in [DATA_CONTRACT.md](DATA_CONTRACT.md).

## The story

This project explores whether NYC housing and construction-related filing activity is associated with serious transportation crashes.

Using DOB NOW Housing filings and DOT SIRTA serious crash records, the team cleaned and integrated data at ZIP-year and borough-month levels, then developed 12 research questions with interactive visualizations.

### Key findings

- **Monthly trends (Q5):** Housing filings and serious crashes show weak same-month correlations across the five boroughs. Lagged patterns vary by borough and do not establish a consistent relationship.
- **ZIP-level association (Q6):** Across 226 ZIP codes, housing filing activity and serious crash counts have a moderate positive association (Pearson r = 0.538; R² = 0.290). Some ZIPs have substantially more or fewer crashes than the fitted regression estimates.
- **Crash timing (Q11):** Crash time-of-day patterns are broadly similar across low-, medium- and high-construction ZIPs, despite large differences in the total number of crashes.
- **Predictive analysis (Q12):** A ZIP-grouped random forest achieves mean ROC AUC of 0.899 when classifying high-crash ZIP-years. Overall filing activity is the strongest feature, but predictive importance is not evidence of causation.

### Why it matters

The dashboard helps explore where housing activity and serious street crashes overlap, how patterns vary geographically and over time, and where further transportation-safety investigation may be useful.

These analyses are exploratory. Housing filings do not directly measure active construction, and SIRTA does not represent every NYC crash. The results should not be interpreted as proof that construction causes crashes.

### Website coverage

The live dashboard includes interactive visualizations for all 12 research questions (Q1–Q12).

Q3 includes an additional borough-level comparison, and Q5 includes a separate monthly lag-correlation chart. Q7 also includes a data-coverage visualization.

Users can select borough, year, housing measure and crash measure filters, then click **Generate Report** to update the charts. Some analyses use a fixed dataset or ignore certain filters where necessary for their methodology; these exceptions are explained in the chart captions.


## Repo structure

```
data/raw/        raw downloads (not committed)
data/clean/      cleaned and integrated files used by the app
notebooks/       analysis notebooks
src/             loaders, cleaning helpers, shared filter, chart functions
app/             Dash website
docs/            prompt log and contributions
```

## Setup

```bash
git clone https://github.com/emilysalama/nyc-housing-safety.git
cd nyc-housing-safety
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-notebook.txt
```

## Running the notebook

Open `notebooks/master_notebook.ipynb` in Jupyter or VS Code and run the cells top to bottom. The repository also includes cleaned and integrated datasets under `data/clean/`. Some data-preparation steps may require downloading the original NYC Open Data sources.

## Running the website locally

```bash
pip install -r requirements.txt
python -m app.app
```

Then open http://127.0.0.1:8050.

## Deployment (Render)

1. Create a Web Service on render.com from this GitHub repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app.app:server`
4. Instance type: Free. Render redeploys on every push to `main`. The free tier sleeps when idle, so the first load can take up to a minute.

## Limitations

- SIRTA covers only serious crashes analyzed by the DOT, not all crashes.
- H5 filings are paperwork, not confirmed construction.
- Some crashes had no ZIP and were recovered by spatial join; some remain unlocated. Location coverage differs by year (only 16% of 2022 crashes had an original ZIP), so year-over-year changes can partly reflect coverage.
- Crashes without a location are not random (about 31% were fatal, versus about 5% of the rest).
- ZIP-level counts can reflect population and traffic, and hide differences within a ZIP.
- All findings are associations, not causation.

## Team contributions

| Member | Name | GitHub | Role | Research questions | Data work | Website work | Other |
|---|---|---|---|---|---|---|---|
| M1 | | | Housing data lead | Q1, Q2 | H5 data loading, EDA, cleaning; housing_clean.csv; housing_sites_points.csv | Q1/Q2 chart modules and website integration support | Housing validation plots |
| M2 | | | Crash data lead | Q3, Q4 | SIRTA cleaning; crash_clean.csv; ZIP and borough recovery | Q3/Q4 charts, borough comparison and tier analysis | Validation plots |
| M3 | | | Integration lead | Q5, Q6 | ZIP boundary handling; ZIP-year and borough-month integration; coverage_report.csv | Q5/Q6 analysis provided; chart modules integrated by M6 | Join-grain justification and notebook analysis |
| M4 | Ahmed | AhmedSameh16003382 | Website core | Q7, Q8 | Tested corrected integrated data against the website | Dash app, filters, Generate Report callbacks, Q7/Q8 charts, coverage panel and stylesheet fixes | Q7/Q8 notebook explanations |
| M5 | | hallamnabil | Search, map, and QA | Q9, Q10 | Verified ZIP boundaries and GeoJSON keys | Search parser, Q9 map, Q10 scatter, map styling and interaction testing | Q9/Q10 notebook content |
| M6 | Emily | emilysalama | Story, documentation, delivery | Q11, Q12 | Reviewed teammates' datasets and validated integration results | Q11/Q12 charts, Render deployment, registered and tested Q3–Q6 charts, fixed Q11/Q5 layouts, tested Generate Report | Repository setup, master notebook integration, README, contributions and prompt log; Q12 performance optimization |
