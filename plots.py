"""Matplotlib charts rendered to base64 PNG strings for the templates."""
import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from config import EVENTS  # noqa: E402

INK, MUTED, GRID = "#f1f5f9", "#8b9bb4", "#1c263c"
ACCENT, ACCENT_2, WARN = "#00f0ff", "#0284c7", "#ffb703"
PALETTE = [
    "#00f0ff",  # electric cyan
    "#00ff9d",  # neon emerald
    "#ff2a6d",  # neon magenta
    "#ffb703",  # neon amber
    "#a855f7",  # neon violet
    "#38bdf8",  # sky neon
    "#f43f5e",  # neon rose
    "#84cc16",  # lime neon
    "#22d3ee",  # bright cyan
    "#fb923c",  # neon orange
]


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_facecolor("none")


def _encode(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True, facecolor="none")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def comparative_bar(report, event):
    """Mean result per athlete (± 1 SD) with each athlete's best marked."""
    spec = EVENTS[event]
    df = report.sort_values("athlete_id")
    x = np.arange(len(df))
    fig, ax = plt.subplots(figsize=(8, 3.6), facecolor="none")
    ax.bar(x, df["mean"], yerr=df["std"].fillna(0), color=ACCENT_2, edgecolor=ACCENT,
           linewidth=1.2, capsize=3, error_kw={"ecolor": MUTED, "elinewidth": 1.2}, label="Mean ± 1 SD", alpha=0.8)
    ax.scatter(x, df["best"], color="#ffffff", edgecolor=ACCENT, linewidth=1.5, marker="D", s=28, zorder=3, label="Best")
    lo = min(df["best"].min(), (df["mean"] - df["std"].fillna(0)).min())
    hi = max(df["best"].max(), (df["mean"] + df["std"].fillna(0)).max())
    pad = (hi - lo) * 0.25 or 1
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xticks(x, df["athlete_id"])
    ax.set_ylabel(f"{spec['label']} ({spec['unit']})", color=MUTED, fontsize=9)
    ax.set_ylim(lo - pad, hi + pad / 2)               # bars start from a common floor below the data
    ax.set_title(("Lower is better" if not spec["higher_is_better"] else "Higher is better")
                 + " · axis does not start at zero", loc="left", fontsize=9, color=MUTED)
    _style(ax)
    leg = ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
    if leg:
        for t in leg.get_texts():
            t.set_color(MUTED)
    return _encode(fig)


def cohort_timeseries(athletes, event, highlight=None):
    spec = EVENTS[event]
    fig, ax = plt.subplots(figsize=(8, 3.8), facecolor="none")
    for i, a in enumerate(athletes.values()):
        s, _, v = a.history(event)
        if not len(v):
            continue
        strong = highlight is None or a.athlete_id in highlight
        color = PALETTE[i % len(PALETTE)]
        ax.plot(s, v, marker="o", markersize=4, linewidth=2.2 if strong else 1.2,
                color=color, alpha=1 if strong else 0.25)
        ax.annotate(a.athlete_id, (s[-1], v[-1]), xytext=(5, 0), textcoords="offset points",
                    fontsize=8.5, fontweight="bold", va="center", color=color,
                    alpha=1 if strong else 0.4)
    ax.set_xlabel("Session", color=MUTED, fontsize=9)
    ax.set_ylabel(f"{spec['label']} ({spec['unit']})", color=MUTED, fontsize=9)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    if not spec["higher_is_better"]:
        ax.invert_yaxis()
    _style(ax)
    return _encode(fig)


def athlete_trend(analysis, event):
    """One athlete's series with trend line, biggest jump and the leave-one-out trend."""
    spec = EVENTS[event]
    s, v = analysis["sessions"], analysis["values"]
    fig, ax = plt.subplots(figsize=(7, 3.4), facecolor="none")
    ax.plot(s, v, marker="o", markersize=5, color=ACCENT, linewidth=2.2, label="Result", zorder=3)
    if "slope" in analysis:
        sign = 1 if spec["higher_is_better"] else -1
        xs = np.array([s[0], s[-1]])
        ax.plot(xs, sign * (analysis["slope"] * xs + analysis["intercept"]), "--", color="#ffffff",
                linewidth=1.3, label="Trend (all sessions)", alpha=0.9)
        keep = s != analysis["weakest_session"]
        if keep.sum() >= 2:
            m, b = np.polyfit(s[keep], v[keep], 1)
            ax.plot(xs, m * xs + b, ":", color=WARN, linewidth=1.8,
                    label=f"Trend without session {analysis['weakest_session']}")
        a, b2 = analysis["biggest_jump"]
        ia, ib = int(np.where(s == a)[0][0]), int(np.where(s == b2)[0][0])
        ax.plot([s[ia], s[ib]], [v[ia], v[ib]], color=WARN, linewidth=5, alpha=0.4,
                label="Biggest single jump", zorder=2)
    ax.set_xlabel("Session", color=MUTED, fontsize=9)
    ax.set_ylabel(f"{spec['unit']}", color=MUTED, fontsize=9)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    if not spec["higher_is_better"]:
        ax.invert_yaxis()
    _style(ax)
    leg = ax.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(1, 1))
    if leg:
        for t in leg.get_texts():
            t.set_color(MUTED)
    return _encode(fig)
