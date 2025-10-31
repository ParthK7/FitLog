from config import DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(DATABASE_URL, echo = True)

AsyncSession = async_sessionmaker(bind = engine) # best practice

async def get_db():
    async with AsyncSession() as db:
        yield db