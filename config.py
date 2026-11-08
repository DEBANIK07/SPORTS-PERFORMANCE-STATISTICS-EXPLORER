"""Event definitions shared by every module.

higher_is_better tells the ranking/analysis code which direction counts as
an improvement: lower times are better for track events, longer distances
are better for jumps.  min/max are plausibility limits used by validation.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ATHLETES_FILE = os.path.join(DATA_DIR, "athletes.csv")
RESULTS_FILE = os.path.join(DATA_DIR, "results.csv")

EVENTS = {
    "100m": {"label": "100 m sprint", "unit": "s", "higher_is_better": False, "min": 9.5, "max": 20.0},
    "400m": {"label": "400 m run", "unit": "s", "higher_is_better": False, "min": 43.0, "max": 90.0},
    "long_jump": {"label": "Long jump", "unit": "m", "higher_is_better": True, "min": 2.0, "max": 9.0},
}

SQUADS = ["Junior", "Senior"]
