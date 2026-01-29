from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, DECIMAL, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    accounts = relationship("Account", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    budget = relationship("Budget", back_populates="user")
    recurring_payment = relationship("Recurring Payment", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    starting_balance = Column(DECIMAL)

    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    amount = Column(DECIMAL)
    description = Column(String)
    is_income = Column(Boolean)
    account_id = Column(Integer, ForeignKey("accounts.id"))

    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    month = Column(Integer)
    year = Column(Integer)
    total_amt_planned = Column(DECIMAL)

    items = relationship("BudgetItem", back_populates="budget")


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True)
    planned_amt = Column(DECIMAL)

    budget_id = Column(Integer, ForeignKey("budgets.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))

    budget = relationship("Budget", back_populates="items")
    category = relationship("Category", back_populates="budget_items")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    is_default = Column(Boolean)

    budget_items = relationship("BudgetItem", back_populates="category")
    transaction = relationship("Transaction", back_populates="category")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    target_amount = Column(DECIMAL)
    current_amount = Column(DECIMAL)
    target_date = Column(DateTime)
    priority = Column(Integer)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="goals")


class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount = Column(DECIMAL)
    due_day = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    frequency = Column(String)
    is_active = Column(Boolean)

    reminders = relationship("Reminder", back_populates="recurring_payment")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    send_date = Column(DateTime)
    message = Column(String)
    is_sent = Column(Boolean)

    recurring_payment_id = Column(Integer, ForeignKey("recurring_payments.id"))

    recurring_payment = relationship("RecurringPayment", back_populates="reminders")




