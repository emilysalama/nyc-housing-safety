"""Search mode parser. Pure function: text in, filter values out.
app.py applies the result to the dropdowns; Generate Report then draws the charts."""
import re

YEARS = (2022, 2023, 2024, 2025)  # years in the ZIP-year charts

# (value, regex). Order matters: more specific patterns first, because matched text is masked.
BOROUGH_PATTERNS = [("Staten Island", r"staten\s+island"), ("Bronx", r"bronx"), ("Brooklyn", r"brooklyn"),
                    ("Manhattan", r"manhattan"), ("Queens", r"queens")]
HOUSING_PATTERNS = [("h_sidewalk_shed", r"sidewalk\s+sheds?"), ("h_curb_cut", r"curb\s*cuts?"),
                    ("h_new_building", r"new[\s-]+buildings?"), ("h_demolition", r"demolitions?|demolish\w*"),
                    ("h_alteration_co", r"alterations?"), ("h_proposed_units", r"(?:proposed\s+)?(?:dwelling\s+)?units")]
CRASH_PATTERNS = [("t_non_severe_injuries", r"non[\s-]*severe"), ("t_fatalities", r"fatalit(?:y|ies)|deaths?"),
                  ("t_fatal_crashes", r"fatal"), ("t_severe_injuries", r"severe|injur\w*"),
                  ("t_highway_crashes", r"highways?"), ("t_repeat_location_crashes", r"repeat")]
YEAR_PATTERNS = [(None, r"\b20\d{2}\b")]
# Filler words that carry no filter; "crash(es)" is filler because the crash measure defaults in the dropdown
STOPWORDS = {"in", "the", "of", "and", "for", "with", "show", "me", "at", "to", "a", "an", "all", "by", "on",
             "near", "nyc", "crash", "crashes", "filing", "filings", "permit", "permits", "job", "jobs"}


def _find(text, patterns):
    """Return ([(position, value, matched_text)], text with matches blanked out)."""
    found = []
    for value, pattern in patterns:
        for m in re.finditer(pattern, text):
            found.append((m.start(), value, m.group()))
            text = text[:m.start()] + " " * (m.end() - m.start()) + text[m.end():]  # same length keeps offsets valid
    return sorted(found), text


def _first(found, notes, label):
    values = [v for _, v, _ in found]
    if len(set(values)) > 1:
        notes.append(f"More than one {label} found; using {values[0]}.")
    return values[0] if values else None


def parse_query(text):
    """'Brooklyn 2022 new buildings' -> borough, year, h_metric, t_metric (None = not mentioned), plus notes for the UI."""
    work, notes = (text or "").lower(), []
    boroughs, work = _find(work, BOROUGH_PATTERNS)
    housing, work = _find(work, HOUSING_PATTERNS)
    crash, work = _find(work, CRASH_PATTERNS)
    years, work = _find(work, YEAR_PATTERNS)

    year = None
    for _, _, raw in years:
        y = int(raw)
        if y in YEARS and year is None:
            year = y
        elif y in YEARS and y != year:
            notes.append(f"More than one year found; using {year}.")
        elif y == 2026:
            notes.append("2026 only appears in monthly data; the ZIP-year charts cover 2022 to 2025.")
        elif y not in YEARS:
            notes.append(f"No data for {y}; ignored.")

    leftover = [w for w in re.findall(r"[a-z0-9]+", work) if w not in STOPWORDS]
    if leftover:
        notes.append("Ignored: " + ", ".join(leftover))
    return {"borough": _first(boroughs, notes, "borough"), "year": year,
            "h_metric": _first(housing, notes, "housing measure"),
            "t_metric": _first(crash, notes, "crash measure"), "notes": notes}


if __name__ == "__main__":  # run: python -m src.search
    p = parse_query("Brooklyn 2022 new buildings")
    assert (p["borough"], p["year"], p["h_metric"], p["t_metric"], p["notes"]) == ("Brooklyn", 2022, "h_new_building", None, [])
    p = parse_query("fatal crashes in the Bronx 2024 demolition")
    assert (p["borough"], p["year"], p["h_metric"], p["t_metric"], p["notes"]) == ("Bronx", 2024, "h_demolition", "t_fatal_crashes", [])
    p = parse_query("staten island severe 2026")
    assert p["borough"] == "Staten Island" and p["year"] is None and p["t_metric"] == "t_severe_injuries"
    assert any("2026" in n for n in p["notes"])
    assert parse_query("Queens sidewalk sheds")["h_metric"] == "h_sidewalk_shed"
    assert parse_query("hello world")["notes"] == ["Ignored: hello, world"]
    assert parse_query("")["borough"] is None
    print("search parser tests passed")
