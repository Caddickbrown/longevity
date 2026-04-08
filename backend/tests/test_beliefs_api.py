def test_create_belief(client):
    resp = client.post("/beliefs/", json={"title": "On exercise", "body": "Zone 2 is king.", "tags": ["health"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "On exercise"
    assert data["tags"] == ["health"]


def test_list_beliefs(client):
    client.post("/beliefs/", json={"title": "On sleep", "body": "8 hours minimum."})
    client.post("/beliefs/", json={"title": "On diet", "body": "Mediterranean."})
    resp = client.get("/beliefs/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_belief_by_id(client):
    created = client.post("/beliefs/", json={"title": "On focus", "body": "Deep work blocks."}).json()
    resp = client.get(f"/beliefs/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["body"] == "Deep work blocks."


def test_get_belief_not_found(client):
    resp = client.get("/beliefs/9999")
    assert resp.status_code == 404


def test_multiple_versions_by_title(client):
    for body in ["V1: Sleep 7 hrs.", "V2: Sleep 8 hrs.", "V3: Sleep 8-9 hrs."]:
        client.post("/beliefs/", json={"title": "On sleep", "body": body})
    resp = client.get("/beliefs/by-title/On sleep")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_beliefs_are_immutable(client):
    created = client.post("/beliefs/", json={"title": "On risk", "body": "Take calculated risks."}).json()
    # There's no PUT endpoint — confirm it returns 405
    resp = client.put(f"/beliefs/{created['id']}", json={"title": "On risk", "body": "Avoid all risk."})
    assert resp.status_code == 405
