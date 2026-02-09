import os
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

dir = Path(__file__).resolve().parent
db_path = dir / "budget_app.db"

db_url = f"sqlite:///{db_path.as_posix()}"

engine = create_engine(db_url, connect_args={"check_same_thread": False})

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

