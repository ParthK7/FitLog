# from config import DATABASE_URL
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

load_dotenv()
DATABASE_URL = os.getenv('DB_LINK')
print(DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo = True)

AsyncSession = async_sessionmaker(bind = engine) # best practice

async def get_db():
    async with AsyncSession() as db:
        yield db
