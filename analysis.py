"""NumPy consistency analysis and Pandas event reports.

The key question: is an athlete's improvement consistent across sessions, or
is it driven by one result?  We combine five pieces of evidence:

1. Trend slope   – least-squares line through all sessions (np.polyfit).
2. Hit rate      – share of session-to-session changes that were improvements.
3. Monotonicity  – Spearman rank correlation between session and performance.
4. Dominance     – share of all gains that came from the single biggest jump.
5. Leave-one-out – the weakest trend after removing any one session. If one
                   result is holding the trend up, removing it collapses it.
"""
import numpy as np
import pandas as pd

from config import EVENTS
from validation import rank_scores

MIN_SESSIONS = 4

VERDICTS = {
    "consistent": ("Consistent improvement", "good"),
    "one_result": ("Driven by one result", "warn"),
    "noisy": ("Inconsistent improvement", "warn"),
    "none": ("No clear improvement", "bad"),
    "declining": ("Declining", "bad"),
    "insufficient": ("Too few sessions", "muted"),
}


def _ranks(x):
    """Average ranks (ties share a rank) — used for Spearman correlation."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1)
    for val in np.unique(x):
        mask = x == val
        ranks[mask] = ranks[mask].mean()
    return ranks


def spearman(x, y):
    rx, ry = _ranks(np.asarray(x, float)), _ranks(np.asarray(y, float))
    if np.std(rx) == 0 or np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def consistency_analysis(athlete, event):
    sessions, _, values = athlete.history(event)
    hib = EVENTS[event]["higher_is_better"]
    n = len(values)
    result = {"n": n, "sessions": sessions, "values": values}
    if n < MIN_SESSIONS:
        result.update(verdict_key="insufficient",
                      reasons=[f"Needs at least {MIN_SESSIONS} sessions; has {n}."])
        return _finish(result)

    perf = values if hib else -values            # higher = better from here on
    deltas = np.diff(perf)
    slope, intercept = np.polyfit(sessions, perf, 1)
    span = sessions[-1] - sessions[0]
    trend_gain = slope * span                    # improvement the trend line implies

    gains = deltas[deltas > 0]
    total_gain = float(gains.sum())
    biggest = int(np.argmax(deltas))             # index of biggest jump (between biggest and biggest+1)
    dominance = float(deltas[biggest] / total_gain) if total_gain > 0 else 0.0

    loo = np.array([np.polyfit(np.delete(sessions, i), np.delete(perf, i), 1)[0] for i in range(n)])
    weakest_idx = int(np.argmin(loo))
    loo_ratio = float(loo[weakest_idx] / slope) if slope > 0 else 0.0

    others = np.abs(np.delete(deltas, biggest))
    standout = float(deltas[biggest] / np.median(others)) if others.size and np.median(others) > 0 else 0.0

    rho = spearman(sessions, perf)
    hit_rate = float(np.mean(deltas > 0))

    noise = float(np.std(perf - (slope * sessions + intercept), ddof=2)) if n > 2 else 0.0
    signal_to_noise = float(trend_gain / noise) if noise > 0 else float("inf")

    reasons = []
    if slope <= 0 or trend_gain <= 0:
        key = "declining" if rho <= -0.5 else "none"
        reasons.append("The trend line is flat or getting worse.")
    else:
        fragile = (loo_ratio < 0.5 or dominance >= 0.6) and standout >= 2.5
        steady = hit_rate >= 0.6 and rho >= 0.7 and signal_to_noise >= 2
        if steady and not fragile:
            key = "consistent"
            reasons.append(f"{hit_rate:.0%} of session-to-session changes were improvements.")
            reasons.append(f"Removing any single session still keeps ≥{loo_ratio:.0%} of the trend.")
        elif fragile:
            key = "one_result"
            reasons.append(f"That jump is {standout:.1f}× bigger than a typical session-to-session change.")
            if dominance >= 0.6:
                reasons.append(f"One jump (session {sessions[biggest]}→{sessions[biggest + 1]}) "
                               f"accounts for {dominance:.0%} of all gains.")
            if loo_ratio < 0.5:
                reasons.append(f"Dropping session {sessions[weakest_idx]} cuts the trend to "
                               f"{max(loo_ratio, 0):.0%} of its size.")
        elif signal_to_noise < 1.5:
            key = "none"
            reasons.append("The upward trend is smaller than normal session-to-session noise.")
        else:
            key = "noisy"
            reasons.append(f"Only {hit_rate:.0%} of changes were improvements; "
                           f"rank correlation {rho:+.2f}.")

    unit_slope = slope if hib else -slope        # back to event units (sign as raw values move)
    result.update(
        verdict_key=key, reasons=reasons, slope=float(slope), unit_slope=float(unit_slope),
        intercept=float(intercept), hit_rate=hit_rate, rho=rho, dominance=dominance,
        biggest_jump=(int(sessions[biggest]), int(sessions[biggest + 1])),
        loo_ratio=loo_ratio, weakest_session=int(sessions[weakest_idx]),
        signal_to_noise=signal_to_noise, standout=standout,
    )
    return _finish(result)


def _finish(result):
    label, tone = VERDICTS[result["verdict_key"]]
    result["verdict"], result["tone"] = label, tone
    return result


def event_report(athletes, event):
    """Pandas DataFrame: one row per athlete for an event, ranked by best result."""
    spec = EVENTS[event]
    rows = []
    for a in athletes.values():
        if not a.session_count(event):
            continue
        imp_abs, imp_pct = a.improvement(event)
        c = consistency_analysis(a, event)
        rows.append({
            "athlete_id": a.athlete_id, "squad": a.squad, "sessions": a.session_count(event),
            "mean": a.mean(event), "std": a.std(event), "cv_pct": a.cv(event),
            "best": a.best(event), "latest": a.latest(event),
            "improvement": imp_abs, "improvement_pct": imp_pct,
            "hit_rate": c.get("hit_rate"), "dominance": c.get("dominance"),
            "verdict": c["verdict"], "tone": c["tone"],
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    ranking = rank_scores(dict(zip(df.athlete_id, df.best)), spec["higher_is_better"])
    df["rank"] = df.athlete_id.map({aid: r for r, aid, _ in ranking})
    return df.sort_values(["rank", "athlete_id"]).reset_index(drop=True)


def session_pivot(athletes, event):
    """Athlete × session table of raw results (NaN where a session was missed)."""
    records = [{"athlete_id": a.athlete_id, "session": s, "result": v}
               for a in athletes.values() for s, v in zip(*a.history(event)[::2])]
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).pivot(index="athlete_id", columns="session", values="result")


def squad_summary(report):
    if report.empty:
        return report
    return (report.groupby("squad")
            .agg(athletes=("athlete_id", "count"), mean_result=("mean", "mean"),
                 mean_improvement_pct=("improvement_pct", "mean"),
                 consistent=("verdict", lambda v: int((v == VERDICTS["consistent"][0]).sum())))
            .reset_index())
