"""Regenerate the sample anonymised dataset in data/.  Run: python seed_data.py

Each athlete follows a deliberate pattern so the consistency analysis has
something to tell apart: steady improvers, one-off spikes, a breakthrough,
flat/noisy and declining athletes.
"""
import csv
from datetime import date, timedelta

import numpy as np

from config import ATHLETES_FILE, DATA_DIR, EVENTS, RESULTS_FILE
import os

rng = np.random.default_rng(42)
S = np.arange(1, 9)                                   # 8 sessions

PROFILES = {   # athlete: (squad, improvement fraction per session index 0..7)
    "A01": ("Senior", np.linspace(0, 0.045, 8)),                          # steady improver
    "A02": ("Junior", np.linspace(0, 0.065, 8)),                          # steady, larger gains
    "A03": ("Senior", np.where(S == 6, 0.05, 0.0)),                       # one-off great day
    "A04": ("Junior", np.zeros(8)),                                       # flat / noisy
    "A05": ("Senior", np.linspace(0, -0.035, 8)),                         # declining
    "A06": ("Junior", np.where(S >= 4, 0.045, 0.0)),                      # breakthrough at session 4
    "A07": ("Senior", np.linspace(0, 0.03, 8)),                           # improver with more noise
    "A08": ("Junior", np.where(S == 8, 0.055, 0.0)),                      # only last session good
}
NOISE = {"A04": 0.008, "A07": 0.006}
BASES = {"100m": 12.0, "400m": 56.0, "long_jump": 5.6}
SKIP = {("A04", "400m", 5), ("A07", "long_jump", 3)}  # missed sessions

os.makedirs(DATA_DIR, exist_ok=True)
start = date(2026, 8, 3)
with open(ATHLETES_FILE, "w", newline="") as fa, open(RESULTS_FILE, "w", newline="") as fr:
    wa = csv.writer(fa); wa.writerow(["athlete_id", "squad"])
    wr = csv.writer(fr); wr.writerow(["athlete_id", "event", "session", "date", "result"])
    for aid, (squad, frac) in PROFILES.items():
        wa.writerow([aid, squad])
        for event, spec in EVENTS.items():
            base = BASES[event] * rng.uniform(0.95, 1.06)
            noise = rng.normal(0, NOISE.get(aid, 0.003), 8)
            f = frac + noise
            vals = base * (1 + f) if spec["higher_is_better"] else base * (1 - f)
            for s, v in zip(S, vals):
                if (aid, event, int(s)) in SKIP:
                    continue
                wr.writerow([aid, event, int(s), (start + timedelta(weeks=int(s) - 1)).isoformat(),
                             round(float(np.clip(v, spec["min"], spec["max"])), 2)])
print("Sample data written to", DATA_DIR)
