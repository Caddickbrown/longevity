def test_list_interventions_empty(client):
    response = client.get("/protocols/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_interventions_by_tier(client, db):
    from backend.seed_data.protocols import seed_tier1_protocols
    seed_tier1_protocols(db)

    response = client.get("/protocols/?tier=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(i["tier"] == 1 for i in data)


def test_create_and_get_checklist_entry(client, db):
    from backend.seed_data.protocols import seed_tier1_protocols
    seed_tier1_protocols(db)

    interventions = client.get("/protocols/").json()
    first_id = interventions[0]["id"]

    payload = {
        "intervention_id": first_id,
        "date": "2026-04-07",
        "complied": True,
        "notes": "Took with breakfast",
    }
    response = client.post("/checklist/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["complied"] is True

    response = client.get("/checklist/?date=2026-04-07")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_upsert_checklist_entry(client, db):
    from backend.seed_data.protocols import seed_tier1_protocols
    seed_tier1_protocols(db)

    interventions = client.get("/protocols/").json()
    first_id = interventions[0]["id"]

    # Create
    client.post("/checklist/", json={
        "intervention_id": first_id,
        "date": "2026-04-07",
        "complied": False,
        "notes": "",
    })

    # Upsert (update existing)
    response = client.post("/checklist/", json={
        "intervention_id": first_id,
        "date": "2026-04-07",
        "complied": True,
        "notes": "Done",
    })
    assert response.status_code == 201
    assert response.json()["complied"] is True

    # Should still be only 1 record
    entries = client.get("/checklist/?date=2026-04-07").json()
    assert len(entries) == 1
