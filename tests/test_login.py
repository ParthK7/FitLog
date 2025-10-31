from fastapi import status
import pytest


def test_login_success(client):
    user_data = {
        "username": "testuser",
        "password": "strongpassword",
        "email": "testuser@example.com",
    }
    register_resp = client.post("/register", json=user_data)
    assert register_resp.status_code == status.HTTP_200_OK

    login_payload = {"username_or_email": "testuser", "password": "strongpassword"}
    resp = client.post("/login", json=login_payload)

    assert resp.status_code == status.HTTP_200_OK

    data = resp.json()
    assert "id" in data and isinstance(data["id"], int)
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"

    assert "jwt_token" in data and isinstance(data["jwt_token"], str)
    assert len(data["jwt_token"]) > 0



def test_login_wrong_password(client):
    user_data = {
        "username": "wrongpassuser",
        "password": "rightpassword",
        "email": "wrongpass@example.com",
    }
    register_resp = client.post("/register", json=user_data)
    assert register_resp.status_code == status.HTTP_200_OK

    login_payload = {"username_or_email": "wrongpassuser", "password": "incorrect"}
    resp = client.post("/login", json=login_payload)

    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    body = resp.json()
    assert "detail" in body
    assert body["detail"] == "Incorrect password for given credentials."



def test_login_nonexistent_user(client):
    login_payload = {"username_or_email": "noone", "password": "nopass"}
    resp = client.post("/login", json=login_payload)

    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    body = resp.json()
    assert "detail" in body
    assert body["detail"] == "No user with the given emailID or username found. Register the user and then continue to login."



def test_login_missing_fields(client):
    incomplete = {"username_or_email": "abc"}
    resp = client.post("/login", json=incomplete)

    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    body = resp.json()
    assert "detail" in body
    missing_fields = [err["loc"][1] for err in body["detail"] if len(err.get("loc", [])) > 1]
    assert "password" in missing_fields