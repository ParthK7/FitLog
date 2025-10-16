from fastapi import status

# The `client` fixture is automatically provided by pytest because of your conftest.py
# No need to import it explicitly.

def test_register_user_successfully(client):
    """
    Test that a new user can be registered successfully.
    """
    # 1. Define the registration data
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepassword123"
    }

    # 2. Call the endpoint using the test client
    response = client.post("/register", json=user_data)

    # 3. Assert the response status code is 200 OK
    assert response.status_code == status.HTTP_200_OK

    # 4. Assert the response body contains the new user's data
    response_data = response.json()
    assert "email" in response_data
    assert "username" in response_data
    assert response_data["email"] == "test@example.com"
    assert response_data["username"] == "testuser"
    assert "hashed_password" not in response_data # Ensure password is not returned
    assert "id" in response_data and isinstance(response_data["id"], int)


def test_register_duplicate_email(client):
    """
    Test that a second registration with the same email fails.
    """
    # 1. Register the first user successfully
    user_data_1 = {
        "email": "duplicate@example.com",
        "username": "uniqueuser1",
        "password": "securepassword123"
    }
    response_1 = client.post("/register", json=user_data_1)
    assert response_1.status_code == status.HTTP_200_OK
    
    # The `test_session` fixture in conftest.py handles the cleanup.
    # The database state is reset for the second part of this test function.

    # 2. Attempt to register a second user with the same email
    user_data_2 = {
        "email": "duplicate@example.com",  # Duplicate email
        "username": "uniqueuser2",
        "password": "securepassword123"
    }
    response_2 = client.post("/register", json=user_data_2)

    # 3. Assert the response status code is 400 Bad Request
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    # 4. Assert the response body contains the correct error detail
    response_data = response_2.json()
    assert "detail" in response_data
    assert response_data["detail"] == "A user with this email already exists."


def test_register_duplicate_username(client):
    """
    Test that a second registration with the same username fails.
    """
    # 1. Register the first user successfully
    user_data_1 = {
        "email": "unique@example.com",
        "username": "duplicateuser",
        "password": "securepassword123"
    }
    response_1 = client.post("/register", json=user_data_1)
    assert response_1.status_code == status.HTTP_200_OK

    # 2. Attempt to register a second user with the same username
    user_data_2 = {
        "email": "another@example.com",
        "username": "duplicateuser",  # Duplicate username
        "password": "securepassword123"
    }
    response_2 = client.post("/register", json=user_data_2)

    # 3. Assert the response status code is 400 Bad Request
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    # 4. Assert the response body contains the correct error detail
    response_data = response_2.json()
    assert "detail" in response_data
    assert response_data["detail"] == "A user with this username already exists."


def test_register_with_missing_fields(client):
    """
    Test that a registration request with missing fields fails.
    """
    incomplete_data = {
        "email": "incomplete@example.com",
        # Missing "username" and "password"
    }

    response = client.post("/register", json=incomplete_data)
    
    # The endpoint will likely raise a Pydantic validation error for missing fields.
    # The status code will be 422 Unprocessable Entity.
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Assert that the error detail describes the missing fields
    response_data = response.json()
    assert "detail" in response_data
    errors = [error["loc"][1] for error in response_data["detail"]]
    assert "username" in errors
    assert "password" in errors

