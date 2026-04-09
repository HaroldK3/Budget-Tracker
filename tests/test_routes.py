"""
Tests for /categories and /user routes.

Run:
    pytest tests/test_routes.py -v
"""

import os
import pytest
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
from pydantic import BaseModel

# ── Use /tmp so it's always writable (locally and in CI) ───────────────────

TEST_DB_PATH = "/tmp/test_budget.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Models ──────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name          = Column(String, nullable=False)


# ── Pydantic schema ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email:    str
    password: str
    name:     str


# ── Test DB session ─────────────────────────────────────────────────────────

def get_db():
    pass

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── App & routers ───────────────────────────────────────────────────────────

app = FastAPI()

cat_router = APIRouter(prefix="/categories", tags=["categories"])

@cat_router.get("/")
def get_categories(db=Depends(get_db)):
    return db.query(Category).all()

@cat_router.get("/{category_id}")
def get_one(category_id: int, db=Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

user_router = APIRouter(prefix="/user", tags=["User"])

@user_router.post("/login")
def login_user(email: str, password: str, db=Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")
    if not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect Password.")
    return {"message": f"Welcome {user.name}.", "user_id": user.id}

@user_router.post("/create_user")
def create_user(user: UserCreate, db=Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use.")
    new_user = User(
        email=user.email,
        password_hash=pwd_context.hash(user.password),
        name=user.name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {user.email} created."}

app.include_router(cat_router)
app.include_router(user_router)
app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    # Remove any leftover DB file, then create fresh tables
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture()
def seeded_categories(db):
    cats = [Category(name="Food"), Category(name="Transport")]
    db.add_all(cats)
    db.commit()
    for c in cats:
        db.refresh(c)
    return cats

@pytest.fixture()
def seeded_user(db):
    plain = "TestPass123"
    user = User(
        email="test@example.com",
        password_hash=pwd_context.hash(plain),
        name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, plain


# ═══════════════════════════════════════════════════════════════════════════
# Category tests
# ═══════════════════════════════════════════════════════════════════════════

class TestGetCategories:
    def test_returns_all_categories(self, client, seeded_categories):
        response = client.get("/categories/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_returns_empty_list_when_none(self, client):
        response = client.get("/categories/")
        assert response.status_code == 200
        assert response.json() == []


class TestGetOneCategory:
    def test_returns_correct_category(self, client, seeded_categories):
        target = seeded_categories[0]
        response = client.get(f"/categories/{target.id}")
        assert response.status_code == 200
        assert response.json()["id"] == target.id
        assert response.json()["name"] == target.name

    def test_404_for_nonexistent_id(self, client):
        response = client.get("/categories/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"


# ═══════════════════════════════════════════════════════════════════════════
# User tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateUser:
    def test_creates_user_successfully(self, client):
        payload = {"email": "new@example.com", "password": "pass123", "name": "New User"}
        response = client.post("/user/create_user", json=payload)
        assert response.status_code == 200
        assert "new@example.com" in response.json()["message"]

    def test_duplicate_email_rejected(self, client, seeded_user):
        user, _ = seeded_user
        payload = {"email": user.email, "password": "anything", "name": "Duplicate"}
        response = client.post("/user/create_user", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already in use."


class TestLoginUser:
    def test_valid_login_succeeds(self, client, seeded_user):
        user, plain = seeded_user
        response = client.post("/user/login", params={"email": user.email, "password": plain})
        assert response.status_code == 200
        assert "user_id" in response.json()

    def test_wrong_password_rejected(self, client, seeded_user):
        user, _ = seeded_user
        response = client.post("/user/login", params={"email": user.email, "password": "wrongpass"})
        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect Password."

    def test_unknown_email_rejected(self, client):
        response = client.post("/user/login", params={"email": "ghost@example.com", "password": "any"})
        assert response.status_code == 400
        assert response.json()["detail"] == "User not found."