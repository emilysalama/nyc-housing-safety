"""Q12 (Member 6): Can construction metrics, borough, and year identify ZIPs in the
top quartile of serious street crashes, and which feature matters most?

Method (exploratory pattern-finding, NOT causation):
- Unit of analysis: one row per ZIP and year (zip_year_integrated.csv).
- Target: the ZIP-year is in the top quarter of the outcome (default
  t_crashes_street) WITHIN its own year. Ranking within each year keeps the
  target balanced and avoids mixing in changes in how well crashes were located
  across years (see DATA_CONTRACT.md, D4).
- Model: random forest. Features: housing metrics, borough, year.
- Evaluation: 5-fold cross-validation where all rows of a ZIP stay together
  (GroupKFold), so the model is always tested on ZIPs it has not seen.
- Importance: permutation importance on the held-out ZIPs, measured as the drop
  in ROC AUC when one feature is shuffled. This is more trustworthy than the
  forest's built-in importance, which favors columns with many distinct values.

Usage:
    from src.charts import q12
    fig = q12.make_fig(zip_year_df)

Note for the website (M4): the first fit in a fresh Python process takes about 10 to 15 s
(one-time scikit-learn imports); later fits take a few seconds. scikit-learn is listed in
requirements.txt. Cache the result (for example functools.lru_cache keyed on the filter
values), because refitting on every dropdown change would be slow and meaningless on
small subsets.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

NUMERIC_FEATURES = [
    "h_filings_total", "h_new_building", "h_demolition", "h_alteration_co",
    "h_proposed_units", "h_sidewalk_shed", "h_curb_cut", "h_median_days_permit_to_signoff",
]
LABELS = {
    "h_filings_total": "All filings",
    "h_new_building": "New-building filings",
    "h_demolition": "Demolition filings",
    "h_alteration_co": "Alteration CO filings",
    "h_proposed_units": "Proposed dwelling units",
    "h_sidewalk_shed": "Sidewalk-shed filings",
    "h_curb_cut": "Curb-cut filings",
    "h_median_days_permit_to_signoff": "Median days permit to sign-off",
    "year": "Year",
}


def _feature_label(name: str) -> str:
    if name.startswith("borough_"):
        return "Borough: " + name[len("borough_"):]
    return LABELS.get(name, name)


def build_features(df: pd.DataFrame, outcome: str = "t_crashes_street"):
    """Return (X, y, groups): features, top-quartile target, and ZIP ids for grouping."""
    data = df.copy()
    # Within-year rank of the outcome. Ties share an average rank, so the target
    # is "at least the 75th percentile within the year".
    pct_rank = data.groupby("year")[outcome].rank(method="average", pct=True)
    y = (pct_rank >= 0.75).astype(int)

    numeric = data[NUMERIC_FEATURES].copy()
    # The median is NaN when a ZIP has no new buildings; use 0 as the "none" value.
    numeric["h_median_days_permit_to_signoff"] = numeric["h_median_days_permit_to_signoff"].fillna(0)
    boroughs = pd.get_dummies(data["borough"], prefix="borough").astype(int)
    X = pd.concat([numeric, boroughs, data[["year"]]], axis=1)
    return X, y, data["zip"].astype(str)

# n_repeats=5: each repeat reshuffles one feature on the held-out fold; 5 repeats x 5 folds
# already averages 25 shuffles per feature, enough for a stable ranking.
def compute_importance(df: pd.DataFrame, outcome: str = "t_crashes_street",
                       n_splits: int = 5, n_repeats: int = 5, seed: int = 42):
    """Fit and score the model. Returns (importance_df, mean_auc, positive_share).

    importance_df has one row per feature: feature, label, mean, std (drop in AUC).
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.inspection import permutation_importance
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import GroupKFold
    except ImportError as err:
        raise ImportError("Q12 needs scikit-learn: pip install scikit-learn") from err

    X, y, groups = build_features(df, outcome)
    folds, aucs = [], []
    for train_idx, test_idx in GroupKFold(n_splits=n_splits).split(X, y, groups):
        if y.iloc[test_idx].nunique() < 2:  # AUC is undefined with one class
            continue
        # n_jobs=1 on purpose: n_jobs=-1 spawned a joblib worker pool for every one of the
        # ~700 predict_proba calls made by permutation importance, which took ~94 s on Windows.
        # Single-threaded runs in ~3 s once scikit-learn is imported.
        model = RandomForestClassifier(n_estimators=100, min_samples_leaf=3,
                                       class_weight="balanced", random_state=seed, n_jobs=1)
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        aucs.append(roc_auc_score(y.iloc[test_idx], model.predict_proba(X.iloc[test_idx])[:, 1]))
        result = permutation_importance(model, X.iloc[test_idx], y.iloc[test_idx],
                                        scoring="roc_auc", n_repeats=n_repeats,
                                        random_state=seed)
        folds.append(result.importances_mean)

    if not folds:
        raise ValueError("Not enough data to score the model (need both classes in the test folds).")
    per_fold = np.array(folds)
    importance = pd.DataFrame({
        "feature": X.columns,
        "label": [_feature_label(c) for c in X.columns],
        "mean": per_fold.mean(axis=0),
        "std": per_fold.std(axis=0),
    }).sort_values("mean", ascending=False, ignore_index=True)
    return importance, float(np.mean(aucs)), float(y.mean())


def make_fig(df: pd.DataFrame, outcome: str = "t_crashes_street") -> go.Figure:
    """Bar chart of permutation importance. `df` is the ZIP-by-year table."""
    importance, auc, positive_share = compute_importance(df, outcome)
    plot_df = importance.iloc[::-1]  # largest at the top of a horizontal bar chart

    fig = go.Figure(go.Bar(
        x=plot_df["mean"], y=plot_df["label"], orientation="h",
        error_x=dict(type="data", array=plot_df["std"], thickness=1.2),
        hovertemplate="%{y}<br>AUC drop: %{x:.3f}<extra></extra>",
        marker_color="#c0504d",
    ))
    fig.add_vline(x=0, line_width=1, line_color="gray")
    fig.update_layout(
        title=dict(text="Which features help identify ZIPs in the top quarter for serious street crashes?",
                   x=0.01),
        xaxis_title="Drop in ROC AUC when the feature is shuffled (higher = more useful)",
        yaxis_title=None, height=520, margin=dict(t=90, b=110, l=20, r=30),
        annotations=[dict(
            text=(f"Random forest tested on ZIPs it had not seen (5 folds, mean AUC {auc:.2f}; "
                  f"0.50 = chance). Target: top quarter within each year ({positive_share:.0%} of "
                  "ZIP-years). Bars near zero add little. Exploratory; association, not causation."),
            x=0, y=-0.22, xref="paper", yref="paper", showarrow=False, xanchor="left",
            font=dict(size=11))],
    )
    return fig
