from fastapi import status
import pytest


def test_register_user(client):
    #1. request json data
    user_data = {
        "username": "cristiano7",
        "password": "thegoat",
        "email": "cristiano@mail.com",
    }

    #2. Calling the endpoint
    response = client.post("/register", json=user_data)

    #3. Assert response status code
    assert response.status_code == status.HTTP_200_OK

    #4. Assert response body
    data = response.json()
    assert "email" in data
    assert "username" in data
    assert data["email"] == "cristiano@mail.com"
    assert data["username"] == "cristiano7"
    assert "hashed_password" not in data
    assert "id" in data and isinstance(data["id"], int)


def test_duplicate_username(client):
    first_user_data = {
        "username": "cristiano7",
        "password": "thegoat",
        "email": "cristiano@mail.com",
    }
    response_1 = client.post("/register", json=first_user_data)
    assert response_1.status_code == status.HTTP_200_OK

    second_user_data = {
        "username": "cristiano7",
        "password": "alsothegoat",
        "email": "cr7@mail.com",
    }
    response_2 = client.post("/register", json=second_user_data)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    response_data = response_2.json()
    assert "detail" in response_data
    assert response_data["detail"] == "A user with this username already exists."


def test_duplicate_email(client):
    first_user_data = {
        "username": "cristiano7",
        "password": "thegoat",
        "email": "cristiano@mail.com",
    }
    response_1 = client.post("/register", json=first_user_data)
    assert response_1.status_code == status.HTTP_200_OK

    second_user_data = {
        "username": "cristiano_ronaldo",
        "password": "alsothegoat",
        "email": "cristiano@mail.com",
    }
    response_2 = client.post("/register", json=second_user_data)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    response_data = response_2.json()
    assert "detail" in response_data
    assert response_data["detail"] == "A user with this email already exists."


def test_missing_fields(client):
    incomplete_data = {"username": "helloworld"}

    response = client.post("/register", json=incomplete_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response_data = response.json()
    assert "detail" in response_data
    errors = [error["loc"][1] for error in response_data["detail"]]
    assert "email" in errors
    assert "password" in errors