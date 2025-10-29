from locust import HttpUser, task, between, events
from locust.exception import StopUser
from fastapi import status
import random
import os
import psycopg2

class HelloTester(HttpUser):
    wait_time = between(1, 5)

    @task
    def create_exercise(self):
        auth_headers = {
            "Authorization" : f"Bearer {self.jwt_token}"
        }
        
        exercise_data = {
            "name": random.choice(["Dumbbell Press", "Barbell Row", "Leg Extension"]),
            "description" : ""
        }

        self.client.post("/exercises", json = exercise_data, headers = auth_headers, name="/exercise [POST] authenticated")
        

    def on_start(self):
        random_number = random.randint(1, 1000)

        reg_resp = self.client.post("/register", json = {
            "username" : f"locustest_{random_number}",
            "email" : f"locustest_{random_number}@mail.com",
            "password" : "hello"
        })

        if reg_resp.status_code != status.HTTP_200_OK:
            raise StopUser()

        response = self.client.post("/login", json = {
            "username_or_email" : f"locustest_{random_number}",
            "password" : "hello"
        })

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.jwt_token = data["jwt_token"]
        
        else:
            raise StopUser()


@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    print("\n--- Starting Automatic Test Database Cleanup ---")

    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        print("Test database url is not found hence cannot clean the database.")
        return
    
    try:
        connection = psycopg2.connect(db_url)
        cursor = connection.cursor()

        print("Truncating tables")

        cursor.execute("TRUNCATE TABLE exercises RESTART IDENTITY CASCADE;")
        cursor.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")

        connection.commit()
        cursor.close()
        connection.close()

        print("Test database cleaed; all the load test data has been removed.")

    except Exception as e:
        print(f"ERROR during database cleanup: {e}")
        print("!!! Database may not be clean. Manual check is required. !!!")


