from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL', 'sqlite://./docs.db'), echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Создает все таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def get_db_session():
    """Генератор сессии для работы с БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
