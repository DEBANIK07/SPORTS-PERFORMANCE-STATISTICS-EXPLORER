"""File-based record management: athletes.csv and results.csv."""
import csv
import io
import os

from athlete import Athlete
from config import ATHLETES_FILE, DATA_DIR, RESULTS_FILE
from validation import validate_athlete_id, validate_record, validate_squad

ATHLETE_FIELDS = ["athlete_id", "squad"]
RESULT_FIELDS = ["athlete_id", "event", "session", "date", "result"]


def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path, fields in ((ATHLETES_FILE, ATHLETE_FIELDS), (RESULTS_FILE, RESULT_FIELDS)):
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=fields).writeheader()


def _read(path):
    _ensure_files()
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _append(path, fields, row):
    _ensure_files()
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=fields).writerow({k: row[k] for k in fields})


def _rewrite(path, fields, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows({k: r[k] for k in fields} for r in rows)


def load_athletes():
    """Read both files and build {athlete_id: Athlete}. Bad rows are skipped."""
    athletes = {}
    for row in _read(ATHLETES_FILE):
        ok_id, aid = validate_athlete_id(row.get("athlete_id", ""))
        ok_sq, squad = validate_squad(row.get("squad", ""))
        if ok_id and ok_sq:
            athletes[aid] = Athlete(aid, squad)
    for row in _read(RESULTS_FILE):
        ok, clean = validate_record(row, known_athletes=athletes)
        if ok:
            athletes[clean["athlete_id"]].add_result(
                clean["event"], clean["session"], clean["date"], clean["result"])
    return dict(sorted(athletes.items()))


def existing_keys():
    return {(r["athlete_id"], r["event"], int(r["session"])) for r in _read(RESULTS_FILE)}


def add_athlete(athlete_id, squad):
    errors = []
    ok_id, aid = validate_athlete_id(athlete_id)
    ok_sq, sq = validate_squad(squad)
    if not ok_id:
        errors.append(aid)
    if not ok_sq:
        errors.append(sq)
    if ok_id and aid in {r["athlete_id"] for r in _read(ATHLETES_FILE)}:
        errors.append(f"Athlete {aid} already exists.")
    if errors:
        return False, errors
    _append(ATHLETES_FILE, ATHLETE_FIELDS, {"athlete_id": aid, "squad": sq})
    return True, aid


def add_result(row):
    known = {r["athlete_id"] for r in _read(ATHLETES_FILE)}
    ok, out = validate_record(row, existing_keys(), known)
    if ok:
        _append(RESULTS_FILE, RESULT_FIELDS, out)
    return ok, out


def delete_result(athlete_id, event, session):
    rows = _read(RESULTS_FILE)
    keep = [r for r in rows if not (r["athlete_id"] == athlete_id and r["event"] == event
                                    and int(r["session"]) == int(session))]
    _rewrite(RESULTS_FILE, RESULT_FIELDS, keep)
    return len(keep) < len(rows)


def import_results(text):
    """Import a CSV of results. Valid rows are appended; each bad row gets a reason."""
    reader = csv.DictReader(io.StringIO(text))
    missing = set(RESULT_FIELDS) - set(reader.fieldnames or [])
    if missing:
        return 0, [f"File is missing column(s): {', '.join(sorted(missing))}."]
    known = {r["athlete_id"] for r in _read(ATHLETES_FILE)}
    keys = existing_keys()
    added, errors = 0, []
    for line_no, row in enumerate(reader, start=2):
        ok, out = validate_record(row, keys, known)
        if ok:
            _append(RESULTS_FILE, RESULT_FIELDS, out)
            keys.add((out["athlete_id"], out["event"], out["session"]))
            added += 1
        else:
            errors.append(f"Line {line_no}: " + " ".join(out))
    return added, errors


def results_csv_text():
    _ensure_files()
    with open(RESULTS_FILE) as f:
        return f.read()
