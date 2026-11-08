# Sports-Performance Statistics Explorer

A Flask website for analysing event times and scores of anonymised athletes across training sessions.

## Run it

### On Windows
You can simply double-click [`run.bat`](run.bat) to launch the app and automatically open it in your browser/ click on http://127.0.0.1:5000

Or manually in terminal:
```bash
.\.venv\Scripts\python app.py            # open http://127.0.0.1:5000
.\.venv\Scripts\python test_app.py       # run the tests
.\.venv\Scripts\python seed_data.py      # (optional) regenerate sample data
```

## How the brief maps to the code

| Requirement | Where |
|---|---|
| Validate and rank scores with functions | `validation.py`: `validate_score`, `validate_record`, `rank_scores` (competition ranking, direction-aware) |
| Manage athlete/session records in files | `storage.py`: reads/writes `data/athletes.csv` and `data/results.csv`; add, delete, CSV import (row-by-row validation) and export |
| `Athlete` class | `athlete.py`: holds results per event; `mean`, `std`, `cv`, `best`, `improvement`, `session_deltas` |
| NumPy for mean, variability and improvement | `athlete.py` and `analysis.py` (`np.mean`, `np.std`, `np.diff`, `np.polyfit`, `np.corrcoef`) |
| Pandas for event reports | `analysis.py`: `event_report` (ranked DataFrame), `session_pivot`, `squad_summary`; downloadable as CSV |
| Comparative bars and time-series plots | `plots.py`: mean ± SD bars with best marked, cohort time series, per-athlete trend chart |
| Is improvement consistent or driven by one result? | `analysis.consistency_analysis`, explained on the site's **Method** page |

## Consistency assessment

Times are sign-flipped so that higher means better for every event. With 4+ sessions the app computes:
trend slope, gains hit rate, Spearman rank correlation, biggest-jump share (and size versus a typical change),
and a leave-one-out trend (the slope after dropping each session in turn). These give one of these verdicts:
**Consistent improvement**, **Driven by one result**, **Inconsistent improvement**, **No clear improvement**, or **Declining**.

The sample data includes deliberate patterns (steady improvers A01/A02/A07, one-off spikes A03/A08,
a breakthrough A06, flat A04, declining A05) so you can see the verdicts tell them apart.
