"""The Athlete class: holds one anonymised athlete's results and NumPy stats."""
import numpy as np

from config import EVENTS


class Athlete:
    def __init__(self, athlete_id, squad):
        self.athlete_id = athlete_id
        self.squad = squad
        self._results = {}          # event -> {session: (date, value)}

    def __repr__(self):
        return f"Athlete({self.athlete_id!r}, {self.squad!r}, events={self.events})"

    # ---- record management -------------------------------------------------
    def add_result(self, event, session, date, value):
        self._results.setdefault(event, {})[int(session)] = (date, float(value))

    def remove_result(self, event, session):
        return self._results.get(event, {}).pop(int(session), None) is not None

    @property
    def events(self):
        return sorted(e for e, r in self._results.items() if r)

    def session_count(self, event=None):
        if event:
            return len(self._results.get(event, {}))
        return len({s for r in self._results.values() for s in r})

    def history(self, event):
        """Return (sessions, dates, values) sorted by session, as NumPy arrays."""
        rows = sorted(self._results.get(event, {}).items())
        sessions = np.array([s for s, _ in rows], dtype=int)
        dates = [d for _, (d, _) in rows]
        values = np.array([v for _, (_, v) in rows], dtype=float)
        return sessions, dates, values

    # ---- NumPy statistics --------------------------------------------------
    def _hib(self, event):
        return EVENTS[event]["higher_is_better"]

    def mean(self, event):
        _, _, v = self.history(event)
        return float(np.mean(v)) if v.size else None

    def std(self, event):
        """Sample standard deviation (ddof=1) — spread of results."""
        _, _, v = self.history(event)
        return float(np.std(v, ddof=1)) if v.size > 1 else None

    def cv(self, event):
        """Coefficient of variation (%) — variability relative to the mean."""
        m, s = self.mean(event), self.std(event)
        return float(s / m * 100) if m and s is not None else None

    def best(self, event):
        _, _, v = self.history(event)
        if not v.size:
            return None
        return float(np.max(v) if self._hib(event) else np.min(v))

    def latest(self, event):
        _, _, v = self.history(event)
        return float(v[-1]) if v.size else None

    def improvement(self, event):
        """First-to-last change, signed so positive always means 'got better'.

        Returns (absolute change in event units, percent change).
        """
        _, _, v = self.history(event)
        if v.size < 2:
            return None, None
        change = (v[-1] - v[0]) if self._hib(event) else (v[0] - v[-1])
        return float(change), float(change / v[0] * 100)

    def session_deltas(self, event):
        """Session-to-session changes, signed so positive means improvement."""
        _, _, v = self.history(event)
        d = np.diff(v)
        return d if self._hib(event) else -d
