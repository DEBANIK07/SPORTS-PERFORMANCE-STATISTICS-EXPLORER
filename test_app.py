"""Basic tests. Run: python -m pytest -q   (or: python test_app.py)"""
import numpy as np

from analysis import consistency_analysis
from athlete import Athlete
from validation import rank_scores, validate_score, validate_athlete_id


def make(values, event="100m"):
    a = Athlete("A99", "Senior")
    for s, v in enumerate(values, start=1):
        a.add_result(event, s, f"2026-08-{s:02d}", v)
    return a


def test_validation():
    assert validate_score("100m", "11.5") == (True, 11.5)
    assert not validate_score("100m", "abc")[0]
    assert not validate_score("100m", "3")[0]           # implausible
    assert not validate_score("100m", "nan")[0]
    assert not validate_athlete_id("John Smith")[0]     # names rejected
    assert validate_athlete_id("a07") == (True, "A07")


def test_ranking_ties_and_direction():
    assert rank_scores({"A1": 11.0, "A2": 10.5, "A3": 11.0}, False) == [(1, "A2", 10.5), (2, "A1", 11.0), (2, "A3", 11.0)]
    assert rank_scores({"A1": 5.0, "A2": 6.0}, True)[0][1] == "A2"


def test_athlete_stats():
    a = make([12.0, 11.8, 11.6, 11.4])
    assert np.isclose(a.mean("100m"), 11.7)
    assert a.best("100m") == 11.4
    assert np.isclose(a.improvement("100m")[0], 0.6)    # time dropped = positive improvement


def test_verdicts():
    assert consistency_analysis(make([12.0, 11.9, 11.82, 11.7, 11.61, 11.5]), "100m")["verdict_key"] == "consistent"
    assert consistency_analysis(make([12.0, 12.01, 11.99, 12.0, 12.02, 11.4]), "100m")["verdict_key"] == "one_result"
    assert consistency_analysis(make([11.5, 11.6, 11.7, 11.8, 11.9]), "100m")["verdict_key"] == "declining"
    assert consistency_analysis(make([12.0, 11.9]), "100m")["verdict_key"] == "insufficient"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
