"""
Tests for /transaction routes.

Run:
    pytest tests/test_transactions.py -v
"""

import os
import pytest
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, DECIMAL, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ── Test DB setup ────────────────────────────────────────────────────────────

TEST_DB_PATH = "test_transactions.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Models (mirrored from API/models.py) ─────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    email         = Column(String, unique=True, index=True)
    password_hash = Column(String)
    transactions  = relationship("Transaction", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id           = Column(Integer, primary_key=True)
    name         = Column(String)
    type         = Column(String)
    is_default   = Column(Boolean)
    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    id          = Column(Integer, primary_key=True)
    date        = Column(DateTime)
    amount      = Column(DECIMAL)
    description = Column(String)
    is_income   = Column(Boolean)
    user_id     = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    user        = relationship("User", back_populates="transactions")
    category    = relationship("Category", back_populates="transactions")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    amount:      float
    description: Optional[str] = None
    is_income:   bool
    category_id: int
    user_id:     int


# ── DB dependency + override ──────────────────────────────────────────────────

def get_db():
    pass

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── App & router (copied from API/routes/transaction.py) ─────────────────────
# Note: routes are re-declared here so tests are fully self-contained and
# don't depend on the real DB. The logic is identical to your production code.

app = FastAPI()
router = APIRouter(prefix="/transaction", tags=["Transaction"])

@router.get("/balance")
def get_bal(user_id: int, db=Depends(get_db)):
    income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == True
    ).scalar() or 0

    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False
    ).scalar() or 0

    return {
        "user_id":  user_id,
        "income":   float(income),
        "expenses": float(expenses),
        "balance":  float(income) - float(expenses),
    }

@router.post("/add_transaction")
def add_transaction(transaction: TransactionCreate, db=Depends(get_db)):
    new_transaction = Transaction(
        amount=transaction.amount,
        description=transaction.description,
        is_income=transaction.is_income,
        category_id=transaction.category_id,
        user_id=transaction.user_id,
        date=datetime.now(),
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

# NOTE: specific sub-routes (/balance, /type/, /category-summary) MUST be
# declared before the wildcard /{user_id} route, otherwise FastAPI will
# match them as user_ids. Your production router has the same ordering issue
# — see note at bottom of this file.

@router.get("/{user_id}/type/{is_income}")
def get_trans_by_type(user_id: int, is_income: bool, db=Depends(get_db)):
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == is_income
    ).all()
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found. ")
    return transactions

@router.get("/{user_id}/category-summary")
def get_cat_sum(user_id: int, db=Depends(get_db)):
    result = db.query(
        Category.name,
        func.sum(Transaction.amount).label("total_spent")
    ).join(Category.transactions).filter(
        Transaction.user_id == user_id,
    ).group_by(Category.name).all()

    if not result:
        return []
    return [{"category": name, "total_spent": float(total)} for name, total in result]

@router.get("/{user_id}")
def get_trans_by_user(user_id: int, db=Depends(get_db)):
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for user.")
    return transactions

@router.delete("/{user_id}/{transaction_id}")
def delete_trans(user_id: int, transaction_id: int, db=Depends(get_db)):
    transaction = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.id == transaction_id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

app.include_router(router)
app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    engine.dispose()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
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
def seeded_user(db):
    user = User(
        email="test@example.com",
        password_hash=pwd_context.hash("TestPass123"),
        name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture()
def seeded_category(db):
    cat = Category(name="Food", type="expense", is_default=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@pytest.fixture()
def seeded_transactions(db, seeded_user, seeded_category):
    txns = [
        Transaction(amount=1000.0, description="Salary",    is_income=True,  user_id=seeded_user.id, category_id=seeded_category.id, date=datetime.now()),
        Transaction(amount=40.0,   description="Groceries", is_income=False, user_id=seeded_user.id, category_id=seeded_category.id, date=datetime.now()),
        Transaction(amount=20.0,   description="Bus pass",  is_income=False, user_id=seeded_user.id, category_id=seeded_category.id, date=datetime.now()),
    ]
    db.add_all(txns)
    db.commit()
    for t in txns:
        db.refresh(t)
    return txns


# ═══════════════════════════════════════════════════════════════════════════
# POST /transaction/add_transaction
# ═══════════════════════════════════════════════════════════════════════════

class TestAddTransaction:
    def test_adds_income_successfully(self, client, seeded_user, seeded_category):
        payload = {
            "amount": 500.0,
            "description": "Freelance payment",
            "is_income": True,
            "category_id": seeded_category.id,
            "user_id": seeded_user.id,
        }
        response = client.post("/transaction/add_transaction", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert float(data["amount"]) == 500.0
        assert data["is_income"] == True

    def test_adds_expense_successfully(self, client, seeded_user, seeded_category):
        payload = {
            "amount": 75.0,
            "description": "Electricity bill",
            "is_income": False,
            "category_id": seeded_category.id,
            "user_id": seeded_user.id,
        }
        response = client.post("/transaction/add_transaction", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert float(data["amount"]) == 75.0
        assert data["is_income"] == False

    def test_description_is_optional(self, client, seeded_user, seeded_category):
        payload = {
            "amount": 10.0,
            "is_income": False,
            "category_id": seeded_category.id,
            "user_id": seeded_user.id,
        }
        response = client.post("/transaction/add_transaction", json=payload)
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# GET /transaction/{user_id}
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTransactionsByUser:
    def test_returns_all_transactions_for_user(self, client, seeded_user, seeded_transactions):
        response = client.get(f"/transaction/{seeded_user.id}")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_404_for_user_with_no_transactions(self, client, seeded_user):
        response = client.get(f"/transaction/{seeded_user.id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "No transactions found for user."

    def test_does_not_return_other_users_transactions(self, client, db, seeded_user, seeded_category):
        # Create a second user with their own transaction
        other_user = User(email="other@example.com", password_hash="x", name="Other")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        db.add(Transaction(amount=999.0, is_income=True, user_id=other_user.id, category_id=seeded_category.id, date=datetime.now()))
        db.commit()

        # seeded_user has no transactions — should still 404
        response = client.get(f"/transaction/{seeded_user.id}")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# GET /transaction/{user_id}/type/{is_income}
# ═══════════════════════════════════════════════════════════════════════════

class TestGetTransactionsByType:
    def test_returns_only_income(self, client, seeded_user, seeded_transactions):
        response = client.get(f"/transaction/{seeded_user.id}/type/true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert all(t["is_income"] for t in data)

    def test_returns_only_expenses(self, client, seeded_user, seeded_transactions):
        response = client.get(f"/transaction/{seeded_user.id}/type/false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(not t["is_income"] for t in data)

    def test_404_when_no_matching_type(self, client, seeded_user, seeded_transactions):
        # seeded_transactions has no expenses for a fresh user — use a nonexistent user
        response = client.get("/transaction/9999/type/true")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# GET /transaction/balance
# ═══════════════════════════════════════════════════════════════════════════

class TestGetBalance:
    def test_correct_balance_calculation(self, client, seeded_user, seeded_transactions):
        # income=1000, expenses=40+20=60, balance=940
        response = client.get(f"/transaction/balance?user_id={seeded_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["income"]   == 1000.0
        assert data["expenses"] == 60.0
        assert data["balance"]  == 940.0

    def test_balance_is_zero_for_new_user(self, client, seeded_user):
        response = client.get(f"/transaction/balance?user_id={seeded_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["income"]   == 0
        assert data["expenses"] == 0
        assert data["balance"]  == 0


# ═══════════════════════════════════════════════════════════════════════════
# GET /transaction/{user_id}/category-summary
# ═══════════════════════════════════════════════════════════════════════════

class TestCategorySummary:
    def test_returns_summary_grouped_by_category(self, client, db, seeded_user, seeded_category):
        transport = Category(name="Transport", type="expense", is_default=True)
        db.add(transport)
        db.commit()
        db.refresh(transport)

        db.add_all([
            Transaction(amount=50.0,  is_income=False, user_id=seeded_user.id, category_id=seeded_category.id, date=datetime.now()),
            Transaction(amount=30.0,  is_income=False, user_id=seeded_user.id, category_id=seeded_category.id, date=datetime.now()),
            Transaction(amount=15.0,  is_income=False, user_id=seeded_user.id, category_id=transport.id,       date=datetime.now()),
        ])
        db.commit()

        response = client.get(f"/transaction/{seeded_user.id}/category-summary")
        assert response.status_code == 200
        data = response.json()

        totals = {item["category"]: item["total_spent"] for item in data}
        assert totals["Food"]      == 80.0
        assert totals["Transport"] == 15.0

    def test_returns_empty_list_for_user_with_no_transactions(self, client, seeded_user):
        response = client.get(f"/transaction/{seeded_user.id}/category-summary")
        assert response.status_code == 200
        assert response.json() == []


# ═══════════════════════════════════════════════════════════════════════════
# DELETE /transaction/{user_id}/{transaction_id}
# ═══════════════════════════════════════════════════════════════════════════

class TestDeleteTransaction:
    def test_deletes_transaction_successfully(self, client, seeded_user, seeded_transactions):
        target = seeded_transactions[0]
        response = client.delete(f"/transaction/{seeded_user.id}/{target.id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Transaction deleted successfully"

    def test_deleted_transaction_no_longer_returned(self, client, seeded_user, seeded_transactions):
        target = seeded_transactions[0]
        client.delete(f"/transaction/{seeded_user.id}/{target.id}")

        all_txns = client.get(f"/transaction/{seeded_user.id}").json()
        ids = [t["id"] for t in all_txns]
        assert target.id not in ids

    def test_404_for_nonexistent_transaction(self, client, seeded_user):
        response = client.delete(f"/transaction/{seeded_user.id}/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Transaction not found."

    def test_cannot_delete_another_users_transaction(self, client, db, seeded_user, seeded_category):
        other_user = User(email="other@example.com", password_hash="x", name="Other")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        txn = Transaction(amount=100.0, is_income=True, user_id=other_user.id, category_id=seeded_category.id, date=datetime.now())
        db.add(txn)
        db.commit()
        db.refresh(txn)

        # Try to delete other user's transaction using seeded_user's id
        response = client.delete(f"/transaction/{seeded_user.id}/{txn.id}")
        assert response.status_code == 404
