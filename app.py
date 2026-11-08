"""Sports-Performance Statistics Explorer — Flask web app.  Run: python app.py"""
from flask import Flask, Response, flash, redirect, render_template, request, url_for

import analysis
import plots
import storage
from config import EVENTS, SQUADS

app = Flask(__name__)
app.secret_key = "change-me-for-deployment"


def _event_arg():
    event = request.args.get("event", "100m")
    return event if event in EVENTS else "100m"


@app.context_processor
def inject_globals():
    return {"EVENTS": EVENTS, "SQUADS": SQUADS}


@app.template_filter("num")
def num(value, digits=2):
    if value is None or value != value:      # None or NaN
        return "—"
    return f"{value:.{digits}f}"


@app.route("/")
def dashboard():
    event = _event_arg()
    athletes = storage.load_athletes()
    squad = request.args.get("squad", "")
    if squad in SQUADS:
        athletes = {k: a for k, a in athletes.items() if a.squad == squad}
    report = analysis.event_report(athletes, event)
    ctx = {"event": event, "spec": EVENTS[event], "squad": squad, "report": report}
    if not report.empty:
        counts = report["verdict"].value_counts()
        ctx.update(
            bar_chart=plots.comparative_bar(report, event),
            line_chart=plots.cohort_timeseries(athletes, event),
            squads=analysis.squad_summary(report),
            pivot=analysis.session_pivot(athletes, event),
            verdict_counts=[(v, int(counts.get(v, 0)), t) for v, t in analysis.VERDICTS.values()
                            if counts.get(v, 0)],
            total_sessions=int(report["sessions"].sum()),
        )
    return render_template("dashboard.html", **ctx)


@app.route("/athlete/<athlete_id>")
def athlete_page(athlete_id):
    athletes = storage.load_athletes()
    athlete = athletes.get(athlete_id)
    if athlete is None:
        flash(f"No athlete {athlete_id}.", "error")
        return redirect(url_for("dashboard"))
    panels = []
    for event in athlete.events:
        c = analysis.consistency_analysis(athlete, event)
        sessions, dates, values = athlete.history(event)
        panels.append({
            "event": event, "spec": EVENTS[event], "a": c, "chart": plots.athlete_trend(c, event),
            "rows": list(zip(sessions, dates, values, [None] + list(athlete.session_deltas(event)))),
            "mean": athlete.mean(event), "std": athlete.std(event), "cv": athlete.cv(event),
            "best": athlete.best(event), "improvement": athlete.improvement(event),
        })
    return render_template("athlete.html", athlete=athlete, panels=panels)


@app.route("/records", methods=["GET", "POST"])
def records():
    if request.method == "POST":
        kind = request.form.get("kind")
        if kind == "athlete":
            ok, out = storage.add_athlete(request.form.get("athlete_id", ""), request.form.get("squad", ""))
            flash(f"Added athlete {out}." if ok else " ".join(out), "ok" if ok else "error")
        elif kind == "result":
            ok, out = storage.add_result(request.form.to_dict())
            if ok:
                flash(f"Saved {out['athlete_id']} · {EVENTS[out['event']]['label']} · session "
                      f"{out['session']}: {out['result']} {EVENTS[out['event']]['unit']}.", "ok")
            else:
                flash(" ".join(out), "error")
        elif kind == "import":
            upload = request.files.get("file")
            if not upload or not upload.filename:
                flash("Choose a CSV file to import.", "error")
            else:
                added, errors = storage.import_results(upload.read().decode("utf-8", errors="replace"))
                flash(f"Imported {added} result(s).", "ok" if added else "error")
                for e in errors[:15]:
                    flash(e, "error")
                if len(errors) > 15:
                    flash(f"…and {len(errors) - 15} more rejected rows.", "error")
        elif kind == "delete":
            ok = storage.delete_result(request.form["athlete_id"], request.form["event"], request.form["session"])
            flash("Result deleted." if ok else "Result not found.", "ok" if ok else "error")
            return redirect(request.form.get("next") or url_for("records"))
        return redirect(url_for("records"))
    athletes = storage.load_athletes()
    next_session = max((a.session_count() for a in athletes.values()), default=0) + 1
    return render_template("records.html", athletes=athletes, next_session=next_session)


@app.route("/export/results.csv")
def export_results():
    return Response(storage.results_csv_text(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=results.csv"})


@app.route("/export/report-<event>.csv")
def export_report(event):
    if event not in EVENTS:
        return redirect(url_for("dashboard"))
    df = analysis.event_report(storage.load_athletes(), event).drop(columns=["tone"], errors="ignore")
    return Response(df.round(4).to_csv(index=False), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=report_{event}.csv"})


@app.route("/method")
def method():
    return render_template("method.html", min_sessions=analysis.MIN_SESSIONS)


if __name__ == "__main__":
    import os
    import socket
    import threading
    import webbrowser

    # Check if port 5000 is already active
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        port_in_use = (s.connect_ex(("127.0.0.1", 5000)) == 0)

    if port_in_use and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("\n[NOTE] Server is already running at http://127.0.0.1:5000!")
        print("Opening http://127.0.0.1:5000 in your web browser...\n")
        webbrowser.open("http://127.0.0.1:5000")
    else:
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            threading.Timer(0.8, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
        app.run(debug=True)
