from tests.conftest import RESEARCHER_ID, RESEARCHER_PASSWORD


def test_scientific_endpoint_rejects_missing_token(anonymous_client):
    response = anonymous_client.get("/api/datasets")

    assert response.status_code == 401


def test_scientific_endpoint_rejects_invalid_token(anonymous_client):
    response = anonymous_client.get(
        "/api/datasets",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_login_returns_a_token_that_opens_the_scientific_api(
    anonymous_client,
    client,
):
    response = anonymous_client.post(
        "/api/auth/login",
        json={
            "researcher_id": RESEARCHER_ID,
            "password": RESEARCHER_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["researcher_id"] == RESEARCHER_ID

    authorized = anonymous_client.get(
        "/api/datasets",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert authorized.status_code == 200


def test_login_rejects_a_wrong_password(anonymous_client, client):
    response = anonymous_client.post(
        "/api/auth/login",
        json={"researcher_id": RESEARCHER_ID, "password": "WrongPass1!"},
    )

    assert response.status_code == 401


def test_registration_rejects_a_duplicate_researcher_id(
    anonymous_client,
    client,
):
    response = anonymous_client.post(
        "/api/auth/register",
        json={
            "researcher_id": RESEARCHER_ID,
            "password": RESEARCHER_PASSWORD,
        },
    )

    assert response.status_code == 409


def test_registration_rejects_a_weak_password(anonymous_client):
    response = anonymous_client.post(
        "/api/auth/register",
        json={"researcher_id": "weak.password.user", "password": "short"},
    )

    assert response.status_code == 422
