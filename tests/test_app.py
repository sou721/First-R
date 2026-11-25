import random
import re

import pytest

from koppen_quiz.app import create_app
from koppen_quiz.data import CITIES, CODES, KNOWLEDGE
from koppen_quiz.koppen import classify
from koppen_quiz.quiz import MODES, _pool, build_quiz, render_question


@pytest.mark.parametrize("name", list(CITIES))
def test_city_data_matches_expected_climate(name):
    c = CITIES[name]
    assert classify(c["temps"], c["precs"], c["southern"]).code == c["code"]


def test_every_climate_has_a_sample_city():
    assert {c["code"] for c in CITIES.values()} == set(CODES)


@pytest.mark.parametrize("temps, precs, expected", [
    ([5] * 12, [50] * 12, "ET"),
    ([-5] * 12, [10] * 12, "EF"),
    ([25] * 12, [5] * 12, "BW"),
    ([27] * 12, [100] * 12, "Af"),
])
def test_simple_cases(temps, precs, expected):
    assert classify(temps, precs).code == expected


def test_classify_requires_12_months():
    with pytest.raises(ValueError):
        classify([1] * 11, [1] * 12)


def test_knowledge_items_well_formed():
    for text, correct, wrongs, expl in KNOWLEDGE:
        assert len(wrongs) == 3 and correct not in wrongs and len(set(wrongs)) == 3


@pytest.mark.parametrize("mode", list(MODES))
def test_build_quiz_options_are_valid(mode):
    rng = random.Random(0)
    qs = build_quiz(mode, 20, rng)
    assert len(qs) == min(20, len(_pool(mode)))
    for q in qs:
        view = render_question(q)
        assert len(view["options"]) == 4 == len(set(view["options"]))
        assert 0 <= view["answer_index"] < 4


@pytest.fixture
def client():
    return create_app({"TESTING": True, "SECRET_KEY": "test"}).test_client()


def test_full_quiz_flow(client):
    assert client.get("/").status_code == 200
    r = client.post("/start", data={"mode": "mix", "count": "5"})
    assert r.status_code == 302
    for _ in range(5):
        page = client.get("/quiz").get_data(as_text=True)
        assert "第" in page
        r = client.post("/answer", data={"choice": "0"})
        assert r.status_code == 302
        page = client.get("/quiz?show=1").get_data(as_text=True)
        assert "正解" in page
    r = client.get("/quiz")
    assert r.headers["Location"].endswith("/result")
    page = client.get("/result").get_data(as_text=True)
    assert re.search(r"結果：\d / 5", page)


def test_reference_and_check(client):
    assert "雨温図" in client.get("/reference").get_data(as_text=True)
    assert client.get("/check?sample=東京").status_code == 200
    data = {**{f"t{i}": t for i, t in enumerate(CITIES["ロンドン"]["temps"])},
            **{f"p{i}": p for i, p in enumerate(CITIES["ロンドン"]["precs"])}}
    page = client.post("/check", data=data).get_data(as_text=True)
    assert "判定結果：Cfb" in page
    page = client.post("/check", data={"t0": "abc"}).get_data(as_text=True)
    assert "数値で入力" in page
