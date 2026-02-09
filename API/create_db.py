from sqlalchemy import create_engine
from models import Base

engine = create_engine("sqlite:///budget_app.db", echo=True)

Base.metadata.create_all(engine)

print("Database and tables created successfully!")
