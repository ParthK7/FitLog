from locust import HttpUser, task, between, events, SequentialTaskSet
from locust.exception import StopUser
from fastapi import status
import random
import os
import psycopg2
from dotenv import load_dotenv

class UserFlow(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.all_exercises = ["Dumbbell Press", "Barbell Row", "Leg Extension", "Bench Press", "Overhead Press", "Squat"]

    def on_start(self):
        self.exercise_list = list(self.all_exercises)
        random_number = random.randint(1, 100000)

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

        self.auth_headers = {
            "Authorization" : f"Bearer {self.jwt_token}"
        }
    
    #1. creating an exercise
    @task
    def create_first_exercise(self):
        if not self.exercise_list:
            raise StopUser()
            
        exercise_name = self.exercise_list.pop()

        exercise_data = {
            "name" : exercise_name,
            "description" : ""
        }

        exercise1_creation = self.client.post("/exercises", json = exercise_data, headers = self.auth_headers)
        if exercise1_creation.status_code == status.HTTP_200_OK:
            exercise1_response = exercise1_creation.json()
            self.exercise1_id = exercise1_response["exercise_id"]
        else:
            raise StopUser()

    #2. creating another exercise
    @task
    def create_second_exercise(self):
        if not self.exercise_list:
            raise StopUser()
            
        exercise_name = self.exercise_list.pop()

        exercise_data = {
            "name" : exercise_name,
            "description" : ""
        }

        exercise2_creation = self.client.post("/exercises", json = exercise_data, headers = self.auth_headers)
        if exercise2_creation.status_code == status.HTTP_200_OK:
            exercise2_response = exercise2_creation.json()
            self.exercise2_id = exercise2_response["exercise_id"]
        else:
            raise StopUser()

    #3. one last exercise
    @task
    def create_third_exercise(self):
        if not self.exercise_list:
            raise StopUser()
            
        exercise_name = self.exercise_list.pop()

        exercise_data = {
            "name" : exercise_name,
            "description" : ""
        }

        exercise3_creation = self.client.post("/exercises", json = exercise_data, headers = self.auth_headers)
        if exercise3_creation.status_code == status.HTTP_200_OK:
            exercise3_response = exercise3_creation.json()
            self.exercise3_id = exercise3_response["exercise_id"]
        else:
            raise StopUser()

    #4. create a workout
    @task
    def create_first_workout(self):
        workout_data = {
            "name" : "General Workout",
            "description" : "",
            "date" : "2025-10-30",
            "start_time": "2025-10-30T22:44:16.599Z"
        }

        workout_resp = self.client.post("/workouts", json = workout_data, headers = self.auth_headers)
        if workout_resp.status_code == status.HTTP_200_OK:
            workout_response = workout_resp.json()
            self.workout1_id = workout_response["workout_id"] 
        else:
            raise StopUser()

    #5. Add first set
    @task
    def add_first_set(self):
        if not hasattr(self, 'workout1_id') or not hasattr(self, 'exercise1_id'):
            return 
            
        set_data = {
            "workout_id": self.workout1_id,
            "exercise_id": self.exercise1_id,
            "set_number": 1,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #6. Add second set
    @task
    def add_second_set(self):
        if not hasattr(self, 'workout1_id') or not hasattr(self, 'exercise1_id'):
            return 
            
        set_data = {
            "workout_id": self.workout1_id,
            "exercise_id": self.exercise1_id,
            "set_number": 2,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #7. Add first set for another exercise
    @task
    def add_first_set_2(self):
        if not hasattr(self, 'workout1_id') or not hasattr(self, 'exercise2_id'):
            return
            
        set_data = {
            "workout_id": self.workout1_id,
            "exercise_id": self.exercise2_id,
            "set_number": 1,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #8. Add second set for another exercise
    @task
    def add_second_set_2(self):
        if not hasattr(self, 'workout1_id') or not hasattr(self, 'exercise2_id'):
            return
            
        set_data = {
            "workout_id": self.workout1_id,
            "exercise_id": self.exercise2_id,
            "set_number": 2,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #9. Calculate PR
    @task
    def calculate_pr1(self):
        self.client.get("/prs", headers = self.auth_headers)

    #10. create another workout
    @task
    def create_second_workout(self):
        workout_data = {
            "name" : "General Workout",
            "description" : "",
            "date" : "2025-11-30",
            "start_time": "2025-10-30T22:44:16.599Z"
        }

        workout_resp = self.client.post("/workouts", json = workout_data, headers = self.auth_headers)
        if workout_resp.status_code == status.HTTP_200_OK:
            workout_response = workout_resp.json()
            self.workout2_id = workout_response["workout_id"] 
        else:
            raise StopUser()

    #11. Add first set of one exercise
    @task
    def add_first_set_3(self):
        if not hasattr(self, 'workout2_id') or not hasattr(self, 'exercise2_id'):
            return
            
        set_data = {
            "workout_id": self.workout2_id,
            "exercise_id": self.exercise2_id,
            "set_number": 1,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #12. Add second set of one exercise
    @task
    def add_second_set_3(self):
        if not hasattr(self, 'workout2_id') or not hasattr(self, 'exercise2_id'):
            return
            
        set_data = {
            "workout_id": self.workout2_id,
            "exercise_id": self.exercise2_id,
            "set_number": 2,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #13. Add first set of another exercise
    @task
    def add_first_set_4(self):
        if not hasattr(self, 'workout2_id') or not hasattr(self, 'exercise3_id'):
            return
            
        set_data = {
            "workout_id": self.workout2_id,
            "exercise_id": self.exercise3_id,
            "set_number": 1,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #14. Add another set of another exercise. 
    @task
    def add_second_set_4(self):
        if not hasattr(self, 'workout2_id') or not hasattr(self, 'exercise3_id'):
            return
            
        set_data = {
            "workout_id": self.workout2_id,
            "exercise_id": self.exercise3_id,
            "set_number": 2,
            "weight": random.randint(50, 200),
            "reps": random.randint(5, 12)
        }

        set_addition = self.client.post("/workoutexercises", json = set_data, headers = self.auth_headers)

    #15. Calculate PR
    @task
    def calculate_pr2(self):
        self.client.get("/prs", headers = self.auth_headers)

    #16. Add one exercise. 
    @task
    def add_final_exercise(self):
        if not self.exercise_list:
            raise StopUser()
            
        exercise_name = self.exercise_list.pop()

        exercise_data = {
            "name" : exercise_name,
            "description" : ""
        }

        exercise4_creation = self.client.post("/exercises", json = exercise_data, headers = self.auth_headers)
        if exercise4_creation.status_code == status.HTTP_200_OK:
            exercise4_response = exercise4_creation.json()
            self.exercise4_id = exercise4_response["exercise_id"]
        else:
            raise StopUser()

    #17. Edit the first exericse 
    @task
    def edit_first_exercise(self):
        if not hasattr(self, 'exercise1_id'):
            return
            
        new_data = {
            "name" : "custom",
            "description" : ""
        }

        exercise_update = self.client.put(f"/exercises/{self.exercise1_id}", json = new_data, headers = self.auth_headers)
        if exercise_update.status_code == status.HTTP_200_OK:
            exercise_update_response = exercise_update.json()
            self.updated_exercise_id = exercise_update_response["exercise_id"]
        else:
            self.updated_exercise_id = self.exercise1_id
            
    #18. Get all exercises
    @task
    def all_exercises1(self):
        self.client.get("/exercises", headers = self.auth_headers)

    #. Get first exercise
    @task
    def first_exercise(self):
        if not hasattr(self, 'updated_exercise_id') and not hasattr(self, 'exercise1_id'):
            return
            
        target_id = getattr(self, 'updated_exercise_id', getattr(self, 'exercise1_id', None))
        
        if target_id:
            self.client.get(f"/exercises/{target_id}", headers = self.auth_headers)

    #get first workout
    @task
    def first_workout(self):
        if not hasattr(self, 'workout1_id'):
            return
            
        self.client.get(f"/workouts/{self.workout1_id}", headers = self.auth_headers)

    #19. Delete the second exercise 
    @task
    def delete_second_exercise(self):
        if not hasattr(self, 'exercise2_id'):
            return
            
        self.client.delete(f"/exercises/{self.exercise2_id}", headers = self.auth_headers)

    #20. Get all exercises.
    @task
    def all_exercises2(self):
        self.client.get("/exercises", headers = self.auth_headers)
        raise StopUser()


class AppUser(HttpUser):
    tasks = [UserFlow]

    wait_time = between(1, 5)


load_dotenv()
@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    print("\n--- Starting Automatic Test Database Cleanup ---")

    db_url = os.environ.get("DB_LINK")

    if not db_url:
        print("Test database url is not found hence cannot clean the database.")
        return

    if "+asyncpg" in db_url:
        clean_db_url = db_url.replace("+asyncpg", "")
    else:
        clean_db_url = db_url
    
    try:
        connection = psycopg2.connect(clean_db_url)
        cursor = connection.cursor()

        print("Truncating tables")

        cursor.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")

        connection.commit()
        cursor.close()
        connection.close()

        print("Test database cleared; all the load test data has been removed.")

    except Exception as e:
        print(f"ERROR during database cleanup: {e}")
        print("!!! Database may not be clean. Manual check is required. !!!")