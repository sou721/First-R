import os
import secrets

from flask import Flask, redirect, render_template, request, session, url_for

from .climograph import climograph_svg, hythergraph_svg
from .data import CITIES, CLIMATES, KNOWLEDGE
from .koppen import MONTHS, classify
from .quiz import MODES, build_quiz, climate_label, render_question

COUNTS = (5, 10, 20)


def deck_context():
    """暗記カード（ハイサーグラフ）の表示データ。"""
    deck = []
    for name, c in CITIES.items():
        res = classify(c["temps"], c["precs"], c["southern"])
        deck.append({"name": name, "country": c["country"], "code": c["code"],
                     "zone": CLIMATES[c["code"]]["zone"], "southern": c["southern"],
                     "label": climate_label(c["code"]), "info": CLIMATES[c["code"]],
                     "steps": res.steps, "svg": hythergraph_svg(c["temps"], c["precs"])})
    zones = {c["zone"]: c["zone_name"] for c in CLIMATES.values()}
    return {"deck": deck, "zones": zones}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(16)
    if test_config:
        app.config.update(test_config)

    @app.route("/")
    def cards():
        return render_template("cards.html", **deck_context())

    @app.route("/menu")
    def index():
        return render_template("index.html", modes=MODES, counts=COUNTS,
                               n_cities=len(CITIES), n_knowledge=len(KNOWLEDGE))

    @app.post("/start")
    def start():
        mode = request.form.get("mode", "mix")
        if mode not in MODES:
            mode = "mix"
        try:
            count = int(request.form.get("count", 10))
        except ValueError:
            count = 10
        if count not in COUNTS:
            count = 10
        session["mode"] = mode
        session["questions"] = build_quiz(mode, count)
        session["answers"] = []
        return redirect(url_for("quiz"))

    @app.route("/quiz")
    def quiz():
        questions = session.get("questions")
        if not questions:
            return redirect(url_for("index"))
        answers = session.get("answers", [])
        idx = len(answers)
        answered = request.args.get("show") == "1" and idx > 0
        if answered:
            idx -= 1
        elif idx >= len(questions):
            return redirect(url_for("result"))
        view = render_question(questions[idx])
        chosen = answers[idx] if answered else None
        score = sum(1 for i, a in enumerate(answers)
                    if a == render_question(questions[i])["answer_index"])
        return render_template("quiz.html", q=view, num=idx + 1, total=len(questions),
                               answered=answered, chosen=chosen, score=score,
                               mode_name=MODES[session.get("mode", "mix")])

    @app.post("/answer")
    def answer():
        questions = session.get("questions")
        answers = session.get("answers", [])
        if not questions or len(answers) >= len(questions):
            return redirect(url_for("index"))
        try:
            choice = int(request.form["choice"])
        except (KeyError, ValueError):
            return redirect(url_for("quiz"))
        answers.append(choice)
        session["answers"] = answers
        return redirect(url_for("quiz", show=1))

    @app.route("/result")
    def result():
        questions = session.get("questions")
        answers = session.get("answers", [])
        if not questions or len(answers) < len(questions):
            return redirect(url_for("index"))
        review = []
        for q, a in zip(questions, answers):
            view = render_question(q)
            review.append({"q": view, "chosen": a, "ok": a == view["answer_index"]})
        score = sum(r["ok"] for r in review)
        return render_template("result.html", review=review, score=score, total=len(review),
                               mode=session.get("mode", "mix"))

    @app.route("/reference")
    def reference():
        cities = [{"name": n, **c, "label": climate_label(c["code"]),
                   "svg": climograph_svg(c["temps"], c["precs"], n)} for n, c in CITIES.items()]
        return render_template("reference.html", climates=CLIMATES, cities=cities)

    @app.route("/check", methods=["GET", "POST"])
    def check():
        sample = request.args.get("sample")
        form = {"temps": [""] * 12, "precs": [""] * 12, "southern": False}
        if sample in CITIES:
            c = CITIES[sample]
            form = {"temps": c["temps"], "precs": c["precs"], "southern": c["southern"]}
        outcome, error = None, None
        if request.method == "POST":
            raw_t = [request.form.get(f"t{i}", "").strip() for i in range(12)]
            raw_p = [request.form.get(f"p{i}", "").strip() for i in range(12)]
            form = {"temps": raw_t, "precs": raw_p, "southern": bool(request.form.get("southern"))}
            try:
                temps = [float(v) for v in raw_t]
                precs = [float(v) for v in raw_p]
                if any(p < 0 for p in precs):
                    raise ValueError
            except ValueError:
                error = "12か月すべての気温と降水量（0以上）を数値で入力してください。"
            else:
                res = classify(temps, precs, form["southern"])
                outcome = {"code": res.code, "label": climate_label(res.code),
                           "info": CLIMATES[res.code], "steps": res.steps,
                           "svg": climograph_svg(temps, precs)}
        return render_template("check.html", months=MONTHS, form=form, outcome=outcome,
                               error=error, cities=list(CITIES))

    return app
