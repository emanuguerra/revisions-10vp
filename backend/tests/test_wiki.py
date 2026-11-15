from app import knowledge


def test_tree_and_page(client):
    themes = client.get("/api/wiki").json()
    paths = [p["path"] for t in themes for p in t["pages"]]
    assert "geographie/climat/effet-de-serre" in paths
    page = client.get("/api/wiki/page/geographie/climat/albedo").json()
    assert page["title"] == "L'albédo" and "rétroaction" in page["body"].lower()
    assert page["units"] == ["geo-climat"] and page["related"]
    assert client.get("/api/wiki/page/geographie/nope").status_code == 404


def test_filter_by_unit(client):
    assert client.get("/api/wiki?unit=geo-climat").json()
    assert client.get("/api/wiki?unit=maths-pythagore").json() == []


def test_search_ignores_accents_and_ranks_title_first(client):
    hits = client.get("/api/wiki/search", params={"q": "albedo"}).json()
    assert hits[0]["path"] == "geographie/climat/albedo"
    hits = client.get("/api/wiki/search", params={"q": "pergelisol fonte"}).json()
    assert hits[0]["path"] == "geographie/climat/banquise-inlandsis-pergelisol"
    assert client.get("/api/wiki/search", params={"q": "?"}).json() == []


def test_load_reports_problems(tmp_path):
    d = tmp_path / "geographie" / "t"
    d.mkdir(parents=True)
    (d / "ok.md").write_text("---\ntitle: A\nsummary: B\nrelated: [geographie/t/absent]\n---\nVoir [x](wiki:x/y/z).\n")
    (d / "noheader.md").write_text("Pas d'en-tête")
    (d / "nosummary.md").write_text("---\ntitle: A\n---\ntexte")
    themes, errors = knowledge.load(tmp_path)
    assert [p.slug for p in themes[0].pages] == ["ok"]
    text = "\n".join(errors)
    for expected in ("missing YAML header", "missing summary", "related page 'geographie/t/absent'", "wiki:x/y/z"):
        assert expected in text
