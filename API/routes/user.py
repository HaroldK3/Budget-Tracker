from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from API.models import User

router = APIRouter(prefix="/user", tags=["User"])

