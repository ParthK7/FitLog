from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def first_function():
    return {"message" : "Hello!"}