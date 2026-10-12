import pytest
import app as aceest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setattr(aceest, "DATABASE", str(database))
    aceest.init_db()
    aceest.app.config.update(TESTING=True)

    with aceest.app.test_client() as test_client:
        yield test_client


def test_home_and_health(client):
    assert client.get("/").status_code == 200
    health = client.get("/health").get_json()
    assert health["status"] == "healthy"


def test_programs_include_expected_options(client):
    data = client.get("/api/programs").get_json()
    expected = {
        "Fat Loss (FL)",
        "Muscle Gain (MG)",
        "Beginner (BG)",
    }
    assert set(data) == expected
    assert data["Fat Loss (FL)"]["factor"] == 22


def test_create_and_retrieve_client_calculates_calories(client):
    response = client.post(
        "/api/clients",
        json={
            "name": "Asha",
            "age": 28,
            "weight": 60,
            "height": 165,
            "program": "Fat Loss (FL)",
            "target_adherence": 80,
        },
    )
    assert response.status_code == 201
    created = response.get_json()
    assert created["calories"] == 1320

    detail = client.get(f"/api/clients/{created['id']}")
    assert detail.get_json()["name"] == "Asha"


def test_client_validation(client):
    assert client.post("/api/clients", json={}).status_code == 400

    bad_program = client.post(
        "/api/clients",
        json={
            "name": "Asha",
            "age": 28,
            "weight": 60,
            "program": "Unknown",
        },
    )
    assert bad_program.status_code == 400


def test_duplicate_client_rejected(client):
    payload = {
        "name": "Asha",
        "age": 28,
        "weight": 60,
        "program": "Beginner (BG)",
    }
    assert client.post(
        "/api/clients", json=payload
    ).status_code == 201
    assert client.post(
        "/api/clients", json=payload
    ).status_code == 409


def test_progress_lifecycle(client):
    created = client.post(
        "/api/clients",
        json={
            "name": "Ravi",
            "age": 31,
            "weight": 75,
            "program": "Muscle Gain (MG)",
        },
    ).get_json()

    response = client.post(
        f"/api/clients/{created['id']}/progress",
        json={
            "adherence": 90,
            "week": "Week 41 - 2026",
            "notes": "Good consistency",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["adherence"] == 90

    progress = client.get(
        f"/api/clients/{created['id']}/progress"
    ).get_json()
    assert len(progress) == 1


def test_progress_validation_and_missing_client(client):
    missing = client.post(
        "/api/clients/999/progress",
        json={"adherence": 50},
    )
    assert missing.status_code == 404

    created = client.post(
        "/api/clients",
        json={
            "name": "Mina",
            "age": 24,
            "weight": 55,
            "program": "Beginner (BG)",
        },
    ).get_json()

    invalid_progress = client.post(
        f"/api/clients/{created['id']}/progress",
        json={"adherence": 150},
    )
    assert invalid_progress.status_code == 400
