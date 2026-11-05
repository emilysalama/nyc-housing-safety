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

TODO: question, key findings, limitations, and benefit to NYC (copy from the website's story section).

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

TODO: open `notebooks/master_notebook.ipynb` and run all cells top to bottom. The notebook downloads the data through `src/load_data.py`.

## Running the website locally

The dummy data is created with python -m src.make_dummy_data

```bash
pip install -r requirements.txt
python app/app.py
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
| M1 | | | Housing data lead | Q1, Q2 | Load and EDA of H5; cleaning; housing_clean.csv; housing_sites_points.csv | | Validation plots |
| M2 | | | Crash data lead | Q3, Q4 | Load and EDA of SIRTA; cleaning; ZIP and borough recovery; crash_clean.csv | | Validation plots |
| M3 | | | Integration lead | Q5, Q6 | ZIP boundary file; both integrated tables; post-integration cleaning; coverage_report.csv | | Justification of join grains |
| M4 | | | Website core | Q7, Q8 | | Dash app structure; shared filter; dropdowns; Generate Report button and callbacks | |
| M5 | | | Search, map, and QA | Q9, Q10 | | Search mode; map components; styling; interaction testing | |
| M6 | Story, documentation, delivery | Q11, Q12 | Set up the repo, notebook structure and README; deployed the site on Render; built the dummy-data generator; added and tested the Q11 and Q12 charts; tuned Q12 from about 94 s to about 3 s. Full details in `docs/contributions.md`. |