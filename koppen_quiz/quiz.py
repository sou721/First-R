"""問題の生成・表示用データの組み立て・採点。

セッション（クッキー）に保存するのは小さな「問題の種」だけにして、
問題文や選択肢の文字列は表示のたびにデータから組み立てる。
"""

import random

from .climograph import climograph_svg
from .data import CITIES, CLIMATES, CODES, KNOWLEDGE
from .koppen import MONTHS, classify

MODES = {
    "mix": "ミックス（全タイプ）",
    "climograph": "雨温図から判定",
    "city": "都市の気候区",
    "feature": "特徴から気候区",
    "knowledge": "用語・基準の知識",
}


def climate_label(code):
    return f"{code}（{CLIMATES[code]['name']}）"


def _climate_options(answer, rng):
    """正解と、まぎらわしい誤答（同じ気候帯を1つ以上）を含む4択の記号リスト。"""
    zone = CLIMATES[answer]["zone"]
    siblings = [c for c in CODES if c != answer and CLIMATES[c]["zone"] == zone]
    others = [c for c in CODES if c != answer and c not in siblings]
    rng.shuffle(siblings)
    rng.shuffle(others)
    picked = siblings[:1]
    rest = siblings[1:] + others
    rng.shuffle(rest)
    options = [answer] + picked + rest[: 3 - len(picked)]
    rng.shuffle(options)
    return options


def _pool(mode):
    items = []
    if mode in ("mix", "climograph"):
        items += [("climograph", name) for name in CITIES]
    if mode in ("mix", "city"):
        items += [("city", name) for name in CITIES]
    if mode in ("mix", "feature"):
        items += [("feature", code) for code in CODES]
    if mode in ("mix", "knowledge"):
        items += [("knowledge", i) for i in range(len(KNOWLEDGE))]
    return items


def build_quiz(mode, count, rng=None):
    rng = rng or random.Random()
    pool = _pool(mode)
    rng.shuffle(pool)
    questions = []
    for kind, key in pool[:count]:
        if kind == "knowledge":
            order = [0, 1, 2, 3]
            rng.shuffle(order)
            questions.append({"k": kind, "key": key, "o": order})
        else:
            answer = CITIES[key]["code"] if kind in ("climograph", "city") else key
            questions.append({"k": kind, "key": key, "o": _climate_options(answer, rng)})
    return questions


def render_question(q):
    """セッションの種から、テンプレートで使う問題データを作る。"""
    kind, key = q["k"], q["key"]
    view = {"kind": kind, "chart": None, "table": None, "hint": None}

    if kind == "knowledge":
        text, correct, wrongs, expl = KNOWLEDGE[key]
        choices = [correct] + wrongs
        view.update(prompt=text,
                    options=[choices[i] for i in q["o"]],
                    answer_index=q["o"].index(0),
                    explanation=expl, steps=[])
        return view

    if kind in ("climograph", "city"):
        city = CITIES[key]
        code = city["code"]
        result = classify(city["temps"], city["precs"], city["southern"])
        if kind == "climograph":
            view["prompt"] = "次の雨温図が示す都市の気候区はどれ？"
            view["hint"] = "南半球の都市です（夏は12〜2月ごろ）。" if city["southern"] else "北半球の都市です。"
            view["chart"] = climograph_svg(city["temps"], city["precs"])
            view["table"] = list(zip(MONTHS, city["temps"], city["precs"]))
            view["reveal"] = f"正体は {key}（{city['country']}）でした。"
        else:
            view["prompt"] = f"{key}（{city['country']}）の気候区はどれ？"
            view["chart_after"] = climograph_svg(city["temps"], city["precs"], key)
            view["reveal"] = f"{key} の雨温図はこのようになります。"
        view["steps"] = result.steps
    else:  # feature
        code = key
        c = CLIMATES[code]
        view["prompt"] = "次の特徴をもつ気候区はどれ？"
        view["hint"] = (f"特徴：{c['feature']}\n植生：{c['vegetation']}\n"
                        f"土壌：{c['soil']}\n主な分布：{c['regions']}")
        view["steps"] = []

    c = CLIMATES[code]
    view.update(options=[climate_label(o) for o in q["o"]],
                answer_index=q["o"].index(code),
                explanation=(f"{climate_label(code)}：{c['feature']} "
                             f"植生は{c['vegetation']}、土壌は{c['soil']}。"))
    return view
