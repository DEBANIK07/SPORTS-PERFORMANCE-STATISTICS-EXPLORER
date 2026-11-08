"""Functions that validate and rank scores.

Every validator returns (ok, value_or_error_message) so callers can show the
reason a record was rejected instead of crashing.
"""
import math
import re
from datetime import date

from config import EVENTS, SQUADS

ATHLETE_ID_PATTERN = re.compile(r"^A\d{2,3}$")   # anonymised IDs only, e.g. A07


def validate_athlete_id(athlete_id):
    athlete_id = str(athlete_id).strip().upper()
    if not ATHLETE_ID_PATTERN.match(athlete_id):
        return False, "Athlete ID must be anonymised, like A01 or A123 (no names)."
    return True, athlete_id


def validate_squad(squad):
    squad = str(squad).strip().title()
    if squad not in SQUADS:
        return False, f"Squad must be one of: {', '.join(SQUADS)}."
    return True, squad


def validate_event(event):
    event = str(event).strip()
    if event not in EVENTS:
        return False, f"Unknown event '{event}'. Valid events: {', '.join(EVENTS)}."
    return True, event


def validate_session(session):
    try:
        session = int(str(session).strip())
    except ValueError:
        return False, "Session must be a whole number."
    if session < 1:
        return False, "Session number must be 1 or higher."
    return True, session


def validate_date(value):
    try:
        return True, date.fromisoformat(str(value).strip()).isoformat()
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format."


def validate_score(event, value):
    """Check that a time/score is numeric, finite and plausible for the event."""
    ok, event = validate_event(event)
    if not ok:
        return False, event
    try:
        score = float(str(value).strip())
    except ValueError:
        return False, "Result must be a number."
    if not math.isfinite(score):
        return False, "Result must be a finite number."
    spec = EVENTS[event]
    if not (spec["min"] <= score <= spec["max"]):
        return False, (f"{spec['label']} result {score} {spec['unit']} is outside the plausible "
                       f"range {spec['min']}–{spec['max']} {spec['unit']}.")
    return True, round(score, 2)


def validate_record(row, existing_keys=frozenset(), known_athletes=None):
    """Validate one result row (dict). Returns (ok, clean_row_or_list_of_errors)."""
    errors, clean = [], {}
    checks = [
        ("athlete_id", validate_athlete_id, row.get("athlete_id", "")),
        ("event", validate_event, row.get("event", "")),
        ("session", validate_session, row.get("session", "")),
        ("date", validate_date, row.get("date", "")),
    ]
    for field, fn, raw in checks:
        ok, out = fn(raw)
        (clean.__setitem__(field, out) if ok else errors.append(out))
    if "event" in clean:
        ok, out = validate_score(clean["event"], row.get("result", ""))
        (clean.__setitem__("result", out) if ok else errors.append(out))
    if known_athletes is not None and "athlete_id" in clean and clean["athlete_id"] not in known_athletes:
        errors.append(f"Athlete {clean['athlete_id']} is not registered.")
    key = (clean.get("athlete_id"), clean.get("event"), clean.get("session"))
    if not errors and key in existing_keys:
        errors.append(f"{key[0]} already has a {key[1]} result for session {key[2]}.")
    return (False, errors) if errors else (True, clean)


def rank_scores(scores, higher_is_better):
    """Rank {athlete_id: score} using standard competition ranking (1, 2, 2, 4).

    Returns a list of (rank, athlete_id, score), best first.
    """
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=higher_is_better)
    ranked, previous, rank = [], None, 0
    for position, (athlete_id, score) in enumerate(ordered, start=1):
        if score != previous:
            rank = position
            previous = score
        ranked.append((rank, athlete_id, score))
    return ranked
