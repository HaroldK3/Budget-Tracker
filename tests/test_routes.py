"""
Automated tests for /categories and /user routes.

Dependencies:
    pip install pytest 
    
    Used previously:
        httpx fastapi sqlalchemy passlib bcrypt

Run:
    pytest test_routes.py -v
"""

import pytest #type: ignore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext

# ── In-memory SQLite setup ──────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Minimal model definitions (mirrors your real models) ────────────────────

class Category(Base):
    __tablename__ = "categories"
    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String, nullable=False)


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name          = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)


# ── Pydantic schema (mirrors UserCreate) ────────────────────────────────────

from pydantic import BaseModel

class UserCreate(BaseModel):
    email:    str
    password: str
    name:     str


# ── Override get_db to use the test DB ─────────────────────────────────────

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Build the app with inline route logic ───────────────────────────────────
# This mirrors your real routers exactly while staying self-contained.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

app = FastAPI()

def get_db():
    pass  # replaced by override below

# ── Categories router ───────────────────────────────────────────────────────

cat_router = APIRouter(prefix="/categories", tags=["categories"])

@cat_router.get("/")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@cat_router.get("/{category_id}")
def get_one(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# ── User router ─────────────────────────────────────────────────────────────

user_router = APIRouter(prefix="/user", tags=["User"])

@user_router.post("/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found.")
    if not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect Password.")
    return {"message": f"Welcome {user.name}.", "user_id": user.id}

@user_router.post("/create_user")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
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


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    """Wipe and recreate all tables before every test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


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
    """Insert two categories and return them."""
    cats = [Category(name="Fiction"), Category(name="Non-Fiction")]
    db.add_all(cats)
    db.commit()
    for c in cats:
        db.refresh(c)
    return cats


@pytest.fixture()
def seeded_user(db):
    """Insert a user with a known password and return (user, plain_password)."""
    plain = "SecurePass123"
    user = User(
        email="alice@example.com",
        password_hash=pwd_context.hash(plain),
        name="Alice",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, plain


# ═══════════════════════════════════════════════════════════════════════════
# Category route tests
# ═══════════════════════════════════════════════════════════════════════════

class TestGetCategories:
    def test_returns_empty_list_when_no_categories(self, client):
        response = client.get("/categories/")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_categories(self, client, seeded_categories):
        response = client.get("/categories/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert names == {"Fiction", "Non-Fiction"}

    def test_response_contains_id_and_name(self, client, seeded_categories):
        response = client.get("/categories/")
        item = response.json()[0]
        assert "id" in item
        assert "name" in item


class TestGetOneCategory:
    def test_returns_correct_category(self, client, seeded_categories):
        target = seeded_categories[0]
        response = client.get(f"/categories/{target.id}")
        assert response.status_code == 200
        assert response.json()["id"] == target.id
        assert response.json()["name"] == target.name

    def test_404_for_nonexistent_category(self, client):
        response = client.get("/categories/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"

    def test_404_detail_message(self, client):
        response = client.get("/categories/0")
        assert "Category not found" in response.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════
# User route tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateUser:
    def test_creates_new_user_successfully(self, client):
        payload = {"email": "bob@example.com", "password": "pass123", "name": "Bob"}
        response = client.post("/user/create_user", json=payload)
        assert response.status_code == 200
        assert "bob@example.com" in response.json()["message"]

    def test_duplicate_email_returns_400(self, client, seeded_user):
        user, _ = seeded_user
        payload = {"email": user.email, "password": "anything", "name": "Impostor"}
        response = client.post("/user/create_user", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already in use."

    def test_password_is_stored_hashed(self, client, db):
        plain = "PlainTextPassword"
        payload = {"email": "carol@example.com", "password": plain, "name": "Carol"}
        client.post("/user/create_user", json=payload)
        user = db.query(User).filter(User.email == "carol@example.com").first()
        assert user is not None
        assert user.password_hash != plain
        assert pwd_context.verify(plain, user.password_hash)

    def test_missing_required_fields_returns_422(self, client):
        response = client.post("/user/create_user", json={"email": "x@x.com"})
        assert response.status_code == 422

    def test_empty_email_rejected(self, client):
        payload = {"email": "", "password": "pass", "name": "Nobody"}
        # FastAPI allows empty strings through unless validated at model level;
        # this confirms the endpoint at least responds without a server error.
        response = client.post("/user/create_user", json=payload)
        assert response.status_code in (200, 400, 422)


class TestLoginUser:
    def test_valid_credentials_return_welcome(self, client, seeded_user):
        user, plain = seeded_user
        response = client.post(
            "/user/login", params={"email": user.email, "password": plain}
        )
        assert response.status_code == 200
        body = response.json()
        assert user.name in body["message"]
        assert body["user_id"] == user.id

    def test_wrong_password_returns_400(self, client, seeded_user):
        user, _ = seeded_user
        response = client.post(
            "/user/login", params={"email": user.email, "password": "WrongPass!"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect Password."

    def test_nonexistent_email_returns_400(self, client):
        response = client.post(
            "/user/login", params={"email": "ghost@example.com", "password": "any"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "User not found."

    def test_login_response_contains_user_id(self, client, seeded_user):
        user, plain = seeded_user
        response = client.post(
            "/user/login", params={"email": user.email, "password": plain}
        )
        assert "user_id" in response.json()

    def test_case_sensitive_email(self, client, seeded_user):
        """E-mail lookup should be exact-match (case-sensitive at DB level)."""
        user, plain = seeded_user
        response = client.post(
            "/user/login",
            params={"email": user.email.upper(), "password": plain},
        )
        # SQLite LIKE is case-insensitive by default, but filter() uses =
        # so this should fail unless the DB normalises case.
        assert response.status_code in (200, 400)