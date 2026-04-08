def test_create_journal_entry(client):
    resp = client.post("/journal/", json={"date": "2026-04-08", "body": "Good day.", "mood": 8, "energy": 7, "tags": ["health"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-04-08"
    assert data["mood"] == 8
    assert data["tags"] == ["health"]


def test_upsert_updates_existing(client):
    client.post("/journal/", json={"date": "2026-04-08", "body": "First version.", "mood": 5})
    resp = client.post("/journal/", json={"date": "2026-04-08", "body": "Updated version.", "mood": 9})
    assert resp.status_code == 200
    assert resp.json()["body"] == "Updated version."
    assert resp.json()["mood"] == 9


def test_get_entry_by_date(client):
    client.post("/journal/", json={"date": "2026-04-08", "body": "Hello."})
    resp = client.get("/journal/2026-04-08")
    assert resp.status_code == 200
    assert resp.json()["body"] == "Hello."


def test_get_entry_not_found(client):
    resp = client.get("/journal/2099-01-01")
    assert resp.status_code == 404


def test_list_entries(client):
    for i in range(3):
        client.post("/journal/", json={"date": f"2026-04-0{i+1}", "body": f"Day {i}"})
    resp = client.get("/journal/")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_list_entries_date_filter(client):
    for i in range(5):
        client.post("/journal/", json={"date": f"2026-04-0{i+1}", "body": f"Day {i}"})
    resp = client.get("/journal/?from_date=2026-04-02&to_date=2026-04-04")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_search_entries(client):
    client.post("/journal/", json={"date": "2026-04-01", "body": "Went for a run today."})
    client.post("/journal/", json={"date": "2026-04-02", "body": "Felt tired, slept early."})
    resp = client.get("/journal/search?q=run")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert "run" in results[0]["body"]
