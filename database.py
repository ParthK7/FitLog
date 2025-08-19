from config import DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL, echo = True)

SessionLocal = sessionmaker(bind = engine) # best practice