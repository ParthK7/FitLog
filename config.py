from dotenv import load_dotenv
import os


load_dotenv()

if os.getenv('DB_LINK'):
    DATABASE_URL = os.getenv('DB_LINK')
else:
    raise ValueError("The database url is not set in .env")