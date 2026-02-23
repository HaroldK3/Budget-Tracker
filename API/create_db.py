from sqlalchemy import create_engine
from API.models import Category
from API.db import Sessionlocal, engine, Base

engine = create_engine("sqlite:///budget_app.db", echo=True)

Base.metadata.create_all(engine)

print("Database and tables created successfully!")

# Example of adding a category to the database
DEFAULT_CATEGORIES = [
    {"name": "Housing",              "type": "need"},
    {"name": "Groceries",            "type": "need"},
    {"name": "Transportation",       "type": "need"},
    {"name": "Utilities",            "type": "need"},
    {"name": "Healthcare",           "type": "need"},
    {"name": "Insurance",            "type": "need"},
    {"name": "Debt Payments",        "type": "savings_debt"},
    {"name": "Education",            "type": "need"},
    {"name": "Savings",              "type": "savings_debt"},
    {"name": "Entertainment",        "type": "want"},
    {"name": "Dining Out",           "type": "want"},
    {"name": "Travel",               "type": "want"},
    {"name": "Hobbies",              "type": "want"},
    {"name": "Clothing",             "type": "want"},
    {"name": "Gifts",                "type": "want"},
    {"name": "Personal Care",        "type": "want"},
    {"name": "Subscriptions",        "type": "want"},
    {"name": "Miscellaneous",        "type": "want"},
]

def seed_categories():
    db = Sessionlocal()
    try:
        from sqlalchemy import func

        count = db.query(func.count(Category.id)).scalar()
        if count == 0:
            for c in DEFAULT_CATEGORIES:
                db.add(Category(
                    name=c["name"],
                    type=c["type"],
                    is_default=True
                ))
            db.commit()
            print("Default categories seeded.")
        else:
            print("Categories already exist, skipping seeding.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()


