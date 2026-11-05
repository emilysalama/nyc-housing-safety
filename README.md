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

TODO: SIRTA covers only serious crashes analyzed by the DOT; some crash locations had missing ZIPs; filings are paperwork, not confirmed construction; all findings are associations, not causation.

## Team contributions

TODO: copy the final table from `docs/contributions.md`.