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


def test_prs_basic(client):
    """Create exercises and workout sets and assert PRs return the max weight per exercise."""
    headers = _get_auth_headers(client, "pruser1", "pw", "pruser1@example.com")

    # Create two exercises
    ex1 = client.post("/exercises", json={"name": "Snatch", "description": ""}, headers=headers)
    assert ex1.status_code == status.HTTP_200_OK
    ex1_id = ex1.json()["exercise_id"]

    ex2 = client.post("/exercises", json={"name": "Clean & Jerk", "description": ""}, headers=headers)
    assert ex2.status_code == status.HTTP_200_OK
    ex2_id = ex2.json()["exercise_id"]

    # Create two workouts and add sets with different weights
    w1 = client.post("/workouts", json={"name": "W1", "description": "", "date": "2025-10-20", "start_time": "2025-10-20T08:00:00"}, headers=headers)
    w2 = client.post("/workouts", json={"name": "W2", "description": "", "date": "2025-10-21", "start_time": "2025-10-21T09:00:00"}, headers=headers)
    assert w1.status_code == status.HTTP_200_OK and w2.status_code == status.HTTP_200_OK
    w1_id = w1.json()["workout_id"]
    w2_id = w2.json()["workout_id"]

    # Add sets: ex1 weights 100 and 110 -> PR 110, ex2 weights 80 and 85 -> PR 85
    s1 = client.post("/workoutexercises", json={"workout_id": w1_id, "exercise_id": ex1_id, "set_number": 1, "weight": 100, "reps": 3}, headers=headers)
    s2 = client.post("/workoutexercises", json={"workout_id": w2_id, "exercise_id": ex1_id, "set_number": 1, "weight": 110, "reps": 2}, headers=headers)
    s3 = client.post("/workoutexercises", json={"workout_id": w1_id, "exercise_id": ex2_id, "set_number": 1, "weight": 80, "reps": 5}, headers=headers)
    s4 = client.post("/workoutexercises", json={"workout_id": w2_id, "exercise_id": ex2_id, "set_number": 1, "weight": 85, "reps": 4}, headers=headers)
    assert s1.status_code == s2.status_code == s3.status_code == s4.status_code == status.HTTP_200_OK

    # Request PRs
    resp = client.get("/prs", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    # Expect two PR entries with correct max weights
    # exercise names are normalized to lowercase in the DB; compare case-insensitively
    name_to_weight = {p["name"].lower(): float(p["weight"]) for p in data}
    assert name_to_weight.get("snatch") == 110.0
    assert name_to_weight.get("clean & jerk") == 85.0


def test_prs_ownership_and_empty(client):
    """Ensure PRs are per-user and empty when user has no data."""
    # User A creates a workout and set
    headers_a = _get_auth_headers(client, "pruserA", "pw", "prA@example.com")
    ex = client.post("/exercises", json={"name": "Row", "description": ""}, headers=headers_a); assert ex.status_code == status.HTTP_200_OK
    ex_id = ex.json()["exercise_id"]
    w = client.post("/workouts", json={"name": "WA", "description": "", "date": "2025-10-22", "start_time": "2025-10-22T07:00:00"}, headers=headers_a); assert w.status_code == status.HTTP_200_OK
    w_id = w.json()["workout_id"]
    client.post("/workoutexercises", json={"workout_id": w_id, "exercise_id": ex_id, "set_number": 1, "weight": 60, "reps": 5}, headers=headers_a)

    # User B has no data -> PRs should be empty
    headers_b = _get_auth_headers(client, "pruserB", "pw", "prB@example.com")
    resp_b = client.get("/prs", headers=headers_b)
    assert resp_b.status_code == status.HTTP_200_OK
    assert resp_b.json() == []

    # User A should see their PR
    resp_a = client.get("/prs", headers=headers_a)
    assert resp_a.status_code == status.HTTP_200_OK
    pr_list = resp_a.json()
    # normalize names to lowercase for comparison
    assert any(p["name"].lower() == "row" and float(p["weight"]) == 60.0 for p in pr_list)
