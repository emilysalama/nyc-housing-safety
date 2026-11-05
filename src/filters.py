"""The one shared filter. Every chart receives the output of filter_df."""
import pandas as pd

ALL = "All"

def filter_df(df: pd.DataFrame, borough=ALL, year=ALL) -> pd.DataFrame:
    """Filter an integrated table by borough and year.
    Works on both integrated tables (both have 'borough' and 'year').
    'All' or None means no filtering on that field."""
    out = df
    if borough not in (None, ALL):
        out = out[out["borough"] == borough]
    if year not in (None, ALL):
        out = out[out["year"] == int(year)]
    return out.copy()
