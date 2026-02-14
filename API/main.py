from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from API.db import Base, engine
from API import models
from API.routes import user

app = FastAPI()

def create_tables():
    Base.metadata.create_all(bind=engine)

app.add_middleware(  #type: ignore bc pylance hates me
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(user.router)
@app.get("/")
def root():
    return{"message": "Budget API running."}

@app.on_event("startup")
def on_startup():
    create_tables()