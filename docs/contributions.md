# Contributions

Each member updates their own row as they work. This table feeds the README.

| Member | Name | GitHub | Role | Research questions | Data work | Website work | Other |
|---|---|---|---|---|---|---|---|
| M1 | | | Housing data lead | Q1, Q2 | Load and EDA of H5; cleaning; housing_clean.csv; housing_sites_points.csv | | Validation plots |
| M2 | | | Crash data lead | Q3, Q4 | Load and EDA of SIRTA; cleaning; ZIP and borough recovery; crash_clean.csv | | Validation plots |
| M3 | | | Integration lead | Q5, Q6 | ZIP boundary file; both integrated tables; post-integration cleaning; coverage_report.csv | | Justification of join grains |
| M4 | | | Website core | Q7, Q8 | | Dash app structure; shared filter; dropdowns; Generate Report button and callbacks | |
| M5 | hallamnabil | hallamnabil | Search, map, and QA | Q9, Q10 | Checked that zip_year_integrated.csv matches the ZIP boundary file (zcta5 key, 5-digit ZIP strings, ZIPs without polygons) | Search mode parser (src/search.py) with tests; Q9 bivariate map and Q10 scatter chart functions; map legend and zoom styling | Q9 and Q10 markdown for the notebook |
| M6 | Story, documentation, delivery | Q11, Q12 | Set up the GitHub repo, notebook structure and README skeleton; ran an early test deployment on Render and deployed the site; added `src/make_dummy_data.py` (dummy files with the contract's column names) so charts could be built before the real data arrived; added and tested the Q11 and Q12 chart functions on dummy data; profiled Q12 with `cProfile` and tuned it from about 94 s to about 3 s (`n_jobs=1`, `n_repeats=5`, kept GroupKFold by ZIP and AUC scoring) |
