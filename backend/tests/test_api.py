from app.models import Question


def solution(db, qid):
    with db() as s:
        return s.get(Question, qid).solution


def test_catalogue(client):
    subjects = client.get("/api/subjects").json()
    slugs = {u["slug"] for s in subjects for u in s["units"]}
    assert {"maths-pythagore", "anglais-metiers"} <= slugs
    unit = client.get("/api/units/maths-pythagore").json()
    assert len(unit["exercises"]) == 8 and len(unit["config"]["levels"]) == 3
    assert "data-widget" in unit["lessons"][0]["blocks"][0]["content"]
    items = client.get("/api/units/anglais-metiers/items?kind=vocab").json()
    assert len(items) == 92


def test_profile_required(client):
    assert client.post("/api/missions", json={"unit": "maths-pythagore"}).status_code == 401


def test_math_mission_with_retry(client, student, db):
    r = client.post("/api/missions", json={"unit": "maths-pythagore", "level": 1}, headers=student)
    assert r.status_code == 200, r.text
    mission = r.json()["mission"]
    assert mission["total"] == 10
    q = r.json()["question"]
    assert q["kind"] == "side" and "answer" not in str(q)

    # wrong side, then the hypotenuse: corrected answer = 5 points
    a = client.post(f"/api/questions/{q['id']}/answer", json={"value": "a"}, headers=student).json()
    assert a["status"] == "retry" and not a["final"] and a["eliminated"] == ["a"]
    a = client.post(f"/api/questions/{q['id']}/answer", json={"value": "c"}, headers=student).json()
    assert a["status"] == "correct" and a["final"] and a["points"] == 5
    assert a["mission"]["score"] == 5 and a["explain"]

    # answer every remaining question right at the first try
    for _ in range(9):
        n = client.post(f"/api/missions/{mission['id']}/next", headers=student).json()
        q = n["question"]
        sol = solution(db, q["id"])
        value = sol["answer"]
        if q["kind"] == "number":
            value = str(value).replace(".", ",")
        a = client.post(f"/api/questions/{q['id']}/answer", json={"value": value}, headers=student).json()
        assert a["status"] == "correct", (q, a)

    end = client.post(f"/api/missions/{mission['id']}/next", headers=student).json()
    assert end["question"] is None and end["mission"]["status"] == "done"
    assert end["mission"]["good"] == 10 and end["mission"]["good_first"] == 9
    # 5 + 9 * 10 + streak bonus from the 3rd first-try answer in a row (7 bonuses)
    assert end["mission"]["score"] == 5 + 90 + 7 * 5
    assert end["best"] == end["mission"]["score"]

    prog = client.get("/api/profiles/me/progress?unit=maths-pythagore", headers=student).json()[0]
    assert prog["answered"] == 10 and prog["best"]["1"] == end["mission"]["score"]


def test_number_retry_then_reveal(client, student, db):
    q = client.post("/api/questions", json={"unit": "maths-pythagore", "exercise": "calcHyp", "level": 0},
                    headers=student).json()
    assert client.post(f"/api/questions/{q['id']}/answer", json={"value": "abc"}, headers=student).json()["status"] == "invalid"
    a = client.post(f"/api/questions/{q['id']}/answer", json={"value": "9999"}, headers=student).json()
    assert a["status"] == "retry" and a["tries"] == 1
    hint = client.post(f"/api/questions/{q['id']}/hint", headers=student).json()["hint"]
    assert hint
    a = client.post(f"/api/questions/{q['id']}/reveal", headers=student).json()
    assert a["final"] and a["status"] == "wrong" and a["points"] == 0 and a["answer_display"]
    assert client.post(f"/api/questions/{q['id']}/answer", json={"value": "1"}, headers=student).status_code == 400


def test_true_false_reveals_after_one_mistake(client, student, db):
    q = client.post("/api/questions", json={"unit": "maths-pythagore", "exercise": "vf"}, headers=student).json()
    wrong = 1 - solution(db, q["id"])["answer"]
    a = client.post(f"/api/questions/{q['id']}/answer", json={"value": wrong}, headers=student).json()
    assert a["final"] and a["status"] == "wrong" and a["correct_answer"] == 1 - wrong


def test_english_quiz_and_review(client, student, db):
    r = client.post("/api/missions", json={"unit": "anglais-metiers", "count": 10, "category": "health"},
                    headers=student).json()
    mid, q = r["mission"]["id"], r["question"]
    seen = []
    for i in range(10):
        sol = solution(db, q["id"])
        seen.append(q["id"])
        if i == 0:  # first question wrong, then corrected: no point (vocab scoring)
            if q["kind"] == "text":
                client.post(f"/api/questions/{q['id']}/answer", json={"value": "zzz"}, headers=student)
                a = client.post(f"/api/questions/{q['id']}/answer", json={"value": sol["answer"][0]}, headers=student).json()
            else:
                wrong = next(i for i in range(len(q["choices"])) if i != sol["answer"])
                client.post(f"/api/questions/{q['id']}/answer", json={"value": wrong}, headers=student)
                a = client.post(f"/api/questions/{q['id']}/answer", json={"value": sol["answer"]}, headers=student).json()
            assert a["status"] == "correct" and a["points"] == 0 and a["speak"]
        else:
            value = sol["answer"][0] if q["kind"] == "text" else sol["answer"]
            a = client.post(f"/api/questions/{q['id']}/answer", json={"value": value}, headers=student).json()
            assert a["points"] == 1
        n = client.post(f"/api/missions/{mid}/next", headers=student).json()
        q = n["question"]
    assert n["mission"]["score"] == 9 and len(n["mistakes"]) == 1
    # every word asked once, all in the chosen topic
    with db() as s:
        keys = [s.get(Question, x).item_key for x in seen]
    assert len(set(keys)) == 10

    review = client.post("/api/missions", json={"unit": "anglais-metiers", "item_keys": [n["mistakes"][0]["item_key"]]},
                         headers=student).json()
    assert review["mission"]["total"] == 1
    with db() as s:
        assert s.get(Question, review["question"]["id"]).item_key == n["mistakes"][0]["item_key"]


def test_topic_with_few_words_shortens_the_quiz(client, student):
    r = client.post("/api/missions", json={"unit": "anglais-metiers", "count": 10, "category": "edu"}, headers=student).json()
    assert r["mission"]["total"] == 6
