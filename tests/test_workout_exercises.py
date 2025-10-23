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


def test_create_workout_exercise_and_duplicate(client):
    headers = _get_auth_headers(client, "weuser1", "pw", "weuser1@example.com")

    # create exercise and workout
    ex = client.post("/exercises", json={"name": "Push", "description": ""}, headers=headers); assert ex.status_code == status.HTTP_200_OK
    ex_id = ex.json()["exercise_id"]
    w = client.post("/workouts", json={"name": "W1", "description": "", "date": "2025-10-23", "start_time": "2025-10-23T07:00:00"}, headers=headers); assert w.status_code == status.HTTP_200_OK
    w_id = w.json()["workout_id"]

    payload = {"workout_id": w_id, "exercise_id": ex_id, "set_number": 1, "weight": 100, "reps": 5}
    r = client.post("/workoutexercises", json=payload, headers=headers)
    assert r.status_code == status.HTTP_200_OK

    # duplicate should return 409
    r2 = client.post("/workoutexercises", json=payload, headers=headers)
    assert r2.status_code == status.HTTP_409_CONFLICT


def test_create_workout_exercise_missing_and_forbidden(client):
    # prepare user A with exercise only
    headers_a = _get_auth_headers(client, "weuser2", "pw", "weuser2@example.com")
    ex = client.post("/exercises", json={"name": "Dip", "description": ""}, headers=headers_a); assert ex.status_code == status.HTTP_200_OK
    ex_id = ex.json()["exercise_id"]

    # User B has a workout
    headers_b = _get_auth_headers(client, "weuser3", "pw", "weuser3@example.com")
    w = client.post("/workouts", json={"name": "WB", "description": "", "date": "2025-10-24", "start_time": "2025-10-24T08:00:00"}, headers=headers_b); assert w.status_code == status.HTTP_200_OK
    w_id = w.json()["workout_id"]

    # Try to create referencing non-existent exercise
    payload_missing_ex = {"workout_id": w_id, "exercise_id": 999999, "set_number": 1, "weight": 50, "reps": 8}
    resp = client.post("/workoutexercises", json=payload_missing_ex, headers=headers_b)
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    # Try to create referencing non-existent workout
    payload_missing_w = {"workout_id": 999999, "exercise_id": ex_id, "set_number": 1, "weight": 50, "reps": 8}
    resp2 = client.post("/workoutexercises", json=payload_missing_w, headers=headers_b)
    assert resp2.status_code == status.HTTP_404_NOT_FOUND

    # Try to create where exercise belongs to someone else
    payload_forbidden = {"workout_id": w_id, "exercise_id": ex_id, "set_number": 1, "weight": 60, "reps": 6}
    resp3 = client.post("/workoutexercises", json=payload_forbidden, headers=headers_b)
    # exercise belongs to user A, workout belongs to user B -> should be 403 for exercise ownership
    assert resp3.status_code == status.HTTP_403_FORBIDDEN


def test_sets_crud_and_ownership(client):
    headers = _get_auth_headers(client, "weuser4", "pw", "weuser4@example.com")
    ex = client.post("/exercises", json={"name": "Clean", "description": ""}, headers=headers); assert ex.status_code == status.HTTP_200_OK
    ex_id = ex.json()["exercise_id"]
    w = client.post("/workouts", json={"name": "W2", "description": "", "date": "2025-10-25", "start_time": "2025-10-25T09:00:00"}, headers=headers); assert w.status_code == status.HTTP_200_OK
    w_id = w.json()["workout_id"]

    # create two sets
    s1 = client.post("/workoutexercises", json={"workout_id": w_id, "exercise_id": ex_id, "set_number": 1, "weight": 80, "reps": 3}, headers=headers); assert s1.status_code == status.HTTP_200_OK
    s2 = client.post("/workoutexercises", json={"workout_id": w_id, "exercise_id": ex_id, "set_number": 2, "weight": 85, "reps": 2}, headers=headers); assert s2.status_code == status.HTTP_200_OK

    # get all sets for workout
    all_sets = client.get(f"/workouts/{w_id}/sets", headers=headers)
    assert all_sets.status_code == status.HTTP_200_OK
    arr = all_sets.json()
    assert any(s["set_number"] == 1 for s in arr) and any(s["set_number"] == 2 for s in arr)

    # get single set
    single = client.get(f"/workouts/{w_id}/sets/{ex_id}/1", headers=headers)
    assert single.status_code == status.HTTP_200_OK

    # edit set
    edit = client.put(f"/workouts/{w_id}/sets/{ex_id}/1", json={"workout_id": w_id, "exercise_id": ex_id, "set_number": 1, "weight": 90, "reps": 4}, headers=headers)
    assert edit.status_code == status.HTTP_200_OK
    assert edit.json()["weight"] == 90

    # delete set
    d = client.delete(f"/workouts/{w_id}/sets/{ex_id}/1", headers=headers)
    assert d.status_code == status.HTTP_204_NO_CONTENT
    # now fetching it returns 404
    g = client.get(f"/workouts/{w_id}/sets/{ex_id}/1", headers=headers)
    assert g.status_code == status.HTTP_404_NOT_FOUND

    # ownership checks: another user cannot access sets
    headers_other = _get_auth_headers(client, "weuser5", "pw", "weuser5@example.com")
    # try to get sets for w_id (belongs to original user)
    forbidden = client.get(f"/workouts/{w_id}/sets", headers=headers_other)
    assert forbidden.status_code == status.HTTP_403_FORBIDDEN
