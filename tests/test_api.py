def sample_record():
    return {
        "sleep_start": "2026-11-02T23:00:00",
        "sleep_end": "2026-11-03T07:00:00",
        "quality": 4,
        "notes": "Хорошо выспался",
    }

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_and_list_record(client):
    response = client.post("/sleep", json=sample_record())
    assert response.status_code == 201
    assert response.json()["quality"] == 4
    listed = client.get("/sleep")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["notes"] == "Хорошо выспался"

def test_reject_invalid_period(client):
    payload = sample_record()
    payload["sleep_end"] = payload["sleep_start"]
    assert client.post("/sleep", json=payload).status_code == 422

def test_update_record(client):
    created = client.post("/sleep", json=sample_record()).json()
    payload = sample_record()
    payload["quality"] = 5
    response = client.put(f"/sleep/{created['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["quality"] == 5

def test_delete_record(client):
    created = client.post("/sleep", json=sample_record()).json()
    assert client.delete(f"/sleep/{created['id']}").status_code == 204
    assert client.get(f"/sleep/{created['id']}").status_code == 404

def test_stats(client):
    client.post("/sleep", json=sample_record())
    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json()["records_count"] == 1
    assert response.json()["average_duration_hours"] == 8.0
