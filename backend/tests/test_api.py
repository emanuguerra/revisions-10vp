from app.models import Question


def solution(db, qid):
    with db() as s:
        return s.get(Question, qid).solution


def test_catalogue(client):
    subjects = client.get("/api/subjects").json()
    slugs = {u["slug"] for s in subjects for u in s["units"]}
    assert {"maths-pythagore", "maths-calcul-litteral", "anglais-metiers"} <= slugs
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
    assert q["kind"] == "side" and q["result"] is None and "explain" not in str(q)

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

    # rewards: 9 first-try answers, 1 corrected, 1 mission, best streak of 9
    rw = client.get("/api/profiles/me/rewards", headers=student).json()
    assert rw["xp"] == 9 * 10 + 5 + 20 and rw["level"] == 2 and rw["level_start"] == 100 and rw["stats"]["best_streak"] == 9
    earned = {b["id"] for b in rw["badges"] if b["earned"]}
    assert {"first-step", "mission-1", "streak-5"} <= earned and "perfect" not in earned
    assert rw["stats"]["days"] == 1

    # a focus session adds XP and a badge; minutes are checked
    assert client.post("/api/profiles/me/focus", json={"minutes": 2}, headers=student).status_code == 422
    rw = client.post("/api/profiles/me/focus", json={"minutes": 15}, headers=student).json()
    assert rw["xp"] == 145 and rw["next_level"] == 300 and "focus-1" in {b["id"] for b in rw["badges"] if b["earned"]}


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


def test_expression_answers(client, student, db):
    q = client.post("/api/questions", json={"unit": "maths-calcul-litteral", "exercise": "developper", "level": 0},
                    headers=student).json()
    assert q["kind"] == "text" and q["result"] is None and "explain" not in str(q)
    expected = solution(db, q["id"])["answer"][0]

    def send(v):
        return client.post(f"/api/questions/{q['id']}/answer", json={"value": v}, headers=student).json()

    # not an expression, or the question itself (equal but not developed): no attempt used
    assert send("x +* 2")["status"] == "invalid"
    a = send(q["prompt"].split("<strong>")[1].split("</strong>")[0])
    assert a["status"] == "invalid" and "parenthèses" in a["message"] and a["tries"] == 0
    a = send("x")
    assert a["status"] == "retry" and a["tries"] == 1
    # any order and spacing is accepted
    terms = expected.replace(" − ", " + −").split(" + ")
    a = send(" + ".join(reversed(terms)).replace("−", "-"))
    assert a["status"] == "correct" and a["points"] == 5


def test_expression_value_must_be_computed(client, student, db):
    q = client.post("/api/questions", json={"unit": "maths-calcul-litteral", "exercise": "valeur", "level": 1},
                    headers=student).json()
    result = int(solution(db, q["id"])["answer"][0])
    a = client.post(f"/api/questions/{q['id']}/answer", json={"value": f"{result - 1} + 1"}, headers=student).json()
    assert a["status"] == "invalid" and a["tries"] == 0
    a = client.post(f"/api/questions/{q['id']}/answer", json={"value": str(result).replace("-", "−")}, headers=student).json()
    assert a["status"] == "correct" and a["points"] == 10


def test_pause_resume_and_review(client, student, db):
    r = client.post("/api/missions", json={"unit": "maths-pythagore", "level": 0}, headers=student).json()
    mid, q = r["mission"]["id"], r["question"]
    client.post(f"/api/questions/{q['id']}/answer", json={"value": "a"}, headers=student)
    client.post(f"/api/questions/{q['id']}/answer", json={"value": "c"}, headers=student)
    q2 = client.post(f"/api/missions/{mid}/next", headers=student).json()["question"]

    # pause = just leave; the mission is listed as active and can be reloaded with its history
    active = client.get("/api/missions/active?unit=maths-pythagore", headers=student).json()
    assert [m["id"] for m in active] == [mid] and active[0]["answered"] == 1 and active[0]["mode"] == "mission"
    full = client.get(f"/api/missions/{mid}", headers=student).json()
    first, current = full["questions"]
    assert first["answers"] == ["a", "c"] and first["result"]["status"] == "correct" and first["result"]["explain"]
    assert current["id"] == q2["id"] and current["result"] is None and "explain" not in str(current)

    # another student cannot read it
    other = {"X-Profile-Token": client.post("/api/profiles", json={"nickname": "B"}).json()["token"]}
    assert client.get(f"/api/missions/{mid}", headers=other).status_code == 404

    # a new mission replaces the paused one
    client.post("/api/missions", json={"unit": "maths-pythagore", "level": 0}, headers=student)
    active = client.get("/api/missions/active?unit=maths-pythagore", headers=student).json()
    assert len(active) == 1 and active[0]["id"] != mid


def test_training_session(client, student, db):
    r = client.post("/api/training", json={"unit": "maths-pythagore", "exercise": "vf", "level": 0},
                    headers=student).json()
    mid, q = r["mission"]["id"], r["question"]
    assert r["mission"]["mode"] == "training" and r["mission"]["exercise"] == "Vrai ou faux ?"
    for _ in range(4):
        client.post(f"/api/questions/{q['id']}/answer", json={"value": solution(db, q["id"])["answer"]}, headers=student)
        n = client.post(f"/api/missions/{mid}/next", headers=student).json()
        q = n["question"]
        assert q and n["mission"]["status"] == "active"
    m = client.get(f"/api/missions/{mid}", headers=student).json()["mission"]
    assert m["answered"] == 4 and m["good"] == 4 and m["score"] == 4 * 10 + 2 * 5
    # training never counts as a record
    prog = client.get("/api/profiles/me/progress?unit=maths-pythagore", headers=student).json()[0]
    assert prog["best"] == {} and prog["missions_done"] == 0


def test_access_code(client, monkeypatch):
    import app.main as main
    monkeypatch.setattr(main, "ACCESS_CODE", "Secret")
    assert client.get("/api/subjects").status_code == 403
    assert client.get("/api/subjects", headers={"X-Access-Code": "secret"}).status_code == 200
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/access").json() == {"required": True, "ok": False}
    assert client.get("/api/access", headers={"X-Access-Code": "Secret"}).json() == {"required": True, "ok": True}
    monkeypatch.setattr(main, "ACCESS_CODE", "")
    assert client.get("/api/subjects").status_code == 200
