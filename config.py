from dotenv import load_dotenv
import os


load_dotenv()

if os.getenv('DB_LINK'):
    DATABASE_URL = os.getenv('DB_LINK')
else:
    raise ValueError("The database url is not set in .env")

if os.getenv('JWT_SECRET_KEY'):
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
else:
    raise ValueError("The secret key is not set in .env")