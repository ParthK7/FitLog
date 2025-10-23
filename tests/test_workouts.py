from fastapi import status

def _get_auth_headers(client, username: str, password: str, email: str):
    register_payload = {"username": username, "password": password, "email": email}
    reg = client.post("/register", json=register_payload)
    assert reg.status_code == status.HTTP_200_OK

    login_payload = {"username_or_email": username, "password": password}
    login_resp = client.post("/login", json=login_payload)
    assert login_resp.status_code == status.HTTP_200_OK
    token = login_resp.json().get("jwt_token")
    assert token
    return {"Authorization": f"Bearer {token}"}


def test_create_workout(client):
    headers = _get_auth_headers(client, "wuser1", "pw", "wuser1@example.com")

    payload = {
        "name": "Morning Session",
        "description": "Leg day",
        "date": "2025-10-23",
        "start_time": "2025-10-23T07:30:00"
    }
    resp = client.post("/workouts", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["name"] == "Morning Session"
    assert data["description"] == "Leg day"
    assert "workout_id" in data


def test_get_all_and_single_workout(client):
    headers = _get_auth_headers(client, "wuser2", "pw", "wuser2@example.com")

    p1 = {"name": "A", "description": "a", "date": "2025-10-23", "start_time": "2025-10-23T08:00:00"}
    p2 = {"name": "B", "description": "b", "date": "2025-10-24", "start_time": "2025-10-24T09:00:00"}
    r1 = client.post("/workouts", json=p1, headers=headers); assert r1.status_code == status.HTTP_200_OK
    r2 = client.post("/workouts", json=p2, headers=headers); assert r2.status_code == status.HTTP_200_OK

    all_resp = client.get("/workouts", headers=headers)
    assert all_resp.status_code == status.HTTP_200_OK
    arr = all_resp.json()
    ids = {w["workout_id"] for w in arr}
    assert r1.json()["workout_id"] in ids and r2.json()["workout_id"] in ids

    single = client.get(f"/workouts/{r1.json()['workout_id']}", headers=headers)
    assert single.status_code == status.HTTP_200_OK


def test_update_workout(client):
    headers = _get_auth_headers(client, "wuser3", "pw", "wuser3@example.com")
    p = {"name": "S", "description": "x", "date": "2025-10-23", "start_time": "2025-10-23T10:00:00"}
    r = client.post("/workouts", json=p, headers=headers); assert r.status_code == status.HTTP_200_OK
    wid = r.json()["workout_id"]

    update = {"name": "Session Updated", "description": "updated", "date": "2025-10-25", "start_time": "2025-10-25T11:00:00"}
    up = client.put(f"/workouts/{wid}", json=update, headers=headers)
    assert up.status_code == status.HTTP_200_OK
    assert up.json()["name"] == "Session Updated"


def test_delete_workout(client):
    headers = _get_auth_headers(client, "wuser4", "pw", "wuser4@example.com")
    p = {"name": "ToDelete", "description": "del", "date": "2025-10-23", "start_time": "2025-10-23T12:00:00"}
    r = client.post("/workouts", json=p, headers=headers); assert r.status_code == status.HTTP_200_OK
    wid = r.json()["workout_id"]

    d = client.delete(f"/workouts/{wid}", headers=headers)
    assert d.status_code == status.HTTP_204_NO_CONTENT

    get_after = client.get(f"/workouts/{wid}", headers=headers)
    assert get_after.status_code == status.HTTP_404_NOT_FOUND


def test_missing_fields_workout(client):
    headers = _get_auth_headers(client, "wuser5", "pw", "wuser5@example.com")
    resp = client.post("/workouts", json={"name": "no_date"}, headers=headers)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_workout_ownership_forbidden(client):
    headers_a = _get_auth_headers(client, "ownerw", "pw", "ownerw@example.com")
    resp = client.post("/workouts", json={"name": "Own", "description": "x", "date": "2025-10-23", "start_time": "2025-10-23T06:00:00"}, headers=headers_a)
    assert resp.status_code == status.HTTP_200_OK
    wid = resp.json()["workout_id"]

    headers_b = _get_auth_headers(client, "intruderw", "pw", "intruderw@example.com")
    # GET
    g = client.get(f"/workouts/{wid}", headers=headers_b)
    assert g.status_code == status.HTTP_403_FORBIDDEN
    assert g.json().get("detail") == "Forbidden: you do not have permission to access this workout."

    # PUT
    pu = client.put(f"/workouts/{wid}", json={"name": "X", "description": "y", "date": "2025-10-23", "start_time": "2025-10-23T06:00:00"}, headers=headers_b)
    assert pu.status_code == status.HTTP_403_FORBIDDEN
    assert pu.json().get("detail") == "Forbidden: you do not have permission to modify this workout."

    # DELETE
    de = client.delete(f"/workouts/{wid}", headers=headers_b)
    assert de.status_code == status.HTTP_403_FORBIDDEN
    assert de.json().get("detail") == "Forbidden: you do not have permission to delete this workout."
