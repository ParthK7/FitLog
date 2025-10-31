from fastapi import status
import pytest


def _get_auth_headers(client, username: str, password: str, email: str):
    """Helper to register and login a user and return Authorization headers.

    We register then login because exercise endpoints require authentication
    via JWT (HTTP Bearer). Returns a dict suitable for the `headers=` arg of
    TestClient requests.
    """
    register_payload = {"username": username, "password": password, "email": email}
    # client call
    reg = client.post("/register", json=register_payload)
    assert reg.status_code == status.HTTP_200_OK

    login_payload = {"username_or_email": username, "password": password}
    # client call
    login_resp = client.post("/login", json=login_payload)
    assert login_resp.status_code == status.HTTP_200_OK
    token = login_resp.json().get("jwt_token")
    assert token
    return {"Authorization": f"Bearer {token}"}


def test_create_exercise(client):
    # helper function call
    headers = _get_auth_headers(client, "exuser", "pass1234", "exuser@example.com")

    payload = {"name": "Bench Press", "description": "Chest exercise"}
    # client call
    resp = client.post("/exercises", json=payload, headers=headers)

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    # The application stores the name as lowercase
    assert data["name"] == "bench press" or data["name"] == "bench press"
    assert "exercise_id" in data and isinstance(data["exercise_id"], int)


def test_get_all_and_single_exercise(client):
    # helper function call
    headers = _get_auth_headers(client, "exuser2", "pass1234", "exuser2@example.com")

    # Create two exercises
    # client calls
    resp1 = client.post("/exercises", json={"name": "Squat", "description": "Legs"}, headers=headers)
    assert resp1.status_code == status.HTTP_200_OK
    id1 = resp1.json()["exercise_id"]

    # client calls
    resp2 = client.post("/exercises", json={"name": "Deadlift", "description": "Back"}, headers=headers)
    assert resp2.status_code == status.HTTP_200_OK
    id2 = resp2.json()["exercise_id"]

    # GET all exercises
    # client call
    all_resp = client.get("/exercises", headers=headers)
    assert all_resp.status_code == status.HTTP_200_OK
    all_data = all_resp.json()
    # At least the two we created should be present
    ids = {e["exercise_id"] for e in all_data}
    assert id1 in ids and id2 in ids

    # GET single exercise
    # client call
    single_resp = client.get(f"/exercises/{id1}", headers=headers)
    assert single_resp.status_code == status.HTTP_200_OK
    single_data = single_resp.json()
    assert single_data["exercise_id"] == id1


def test_update_exercise(client):
    # helper function call
    headers = _get_auth_headers(client, "exuser3", "pass1234", "exuser3@example.com")

    # client calls
    create_resp = client.post("/exercises", json={"name": "OHP", "description": "Shoulders"}, headers=headers)
    assert create_resp.status_code == status.HTTP_200_OK
    eid = create_resp.json()["exercise_id"]

    # Update name and description
    update_payload = {"name": "Overhead Press", "description": "Delts"}
    # client call
    update_resp = client.put(f"/exercises/{eid}", json=update_payload, headers=headers)
    assert update_resp.status_code == status.HTTP_200_OK
    updated = update_resp.json()
    assert updated["name"] == "overhead press"
    assert updated["description"] == "Delts"


def test_delete_exercise(client):
    # helper function call
    headers = _get_auth_headers(client, "exuser4", "pass1234", "exuser4@example.com")

    # client calls
    create_resp = client.post("/exercises", json={"name": "Row", "description": "Back"}, headers=headers)
    assert create_resp.status_code == status.HTTP_200_OK
    eid = create_resp.json()["exercise_id"]

    # client calls
    del_resp = client.delete(f"/exercises/{eid}", headers=headers)
    # delete endpoint returns 204
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # subsequent get should return 404
    # client calls
    get_resp = client.get(f"/exercises/{eid}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_duplicate_exercise_name(client):
    # helper function call
    headers = _get_auth_headers(client, "exuser5", "pass1234", "exuser5@example.com")

    # client calls
    resp1 = client.post("/exercises", json={"name": "Lunge", "description": "Legs"}, headers=headers)
    assert resp1.status_code == status.HTTP_200_OK

    # Creating the same name again should return 400
    # client calls
    resp2 = client.post("/exercises", json={"name": "Lunge", "description": "Legs"}, headers=headers)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert resp2.json().get("detail") == "An exercise with this name already exists. You might want to edit it to make changes."


def test_missing_fields_create_exercise(client):
    # helper function call
    headers = _get_auth_headers(client, "exuser6", "pass1234", "exuser6@example.com")

    # Missing 'name' should produce validation error 422
    # client calls
    resp = client.post("/exercises", json={"description": "No name"}, headers=headers)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    body = resp.json()
    assert "detail" in body
    # ensure 'name' is reported missing
    missing = [err["loc"][1] for err in body["detail"] if len(err.get("loc", [])) > 1]
    assert "name" in missing


def test_exercise_ownership_forbidden(client):
    # User A creates an exercise
    # helper function call
    headers_a = _get_auth_headers(client, "owner", "ownpass", "owner@example.com")
    # client calls
    resp = client.post("/exercises", json={"name": "Pullup", "description": "Back"}, headers=headers_a)
    assert resp.status_code == status.HTTP_200_OK
    eid = resp.json()["exercise_id"]

    # User B attempts to access/modify/delete the same exercise
    # helper function call
    headers_b = _get_auth_headers(client, "intruder", "badpass", "intruder@example.com")

    # GET should return 403 Forbidden
    # client calls
    get_resp = client.get(f"/exercises/{eid}", headers=headers_b)
    assert get_resp.status_code == status.HTTP_403_FORBIDDEN
    assert get_resp.json().get("detail") == "Forbidden: you do not have permission to access this exercise."

    # PUT should return 403 Forbidden
    # client calls
    put_resp = client.put(f"/exercises/{eid}", json={"name": "Pullup Edited", "description": "Back"}, headers=headers_b)
    assert put_resp.status_code == status.HTTP_403_FORBIDDEN
    assert put_resp.json().get("detail") == "Forbidden: you do not have permission to modify this exercise."

    # DELETE should return 403 Forbidden
    # client calls
    del_resp = client.delete(f"/exercises/{eid}", headers=headers_b)
    assert del_resp.status_code == status.HTTP_403_FORBIDDEN
    assert del_resp.json().get("detail") == "Forbidden: you do not have permission to delete this exercise."

