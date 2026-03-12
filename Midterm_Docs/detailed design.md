#Detailed design
##Overall structure
    •	Backend framework: FastAPI for REST API endpoints (auth, transactions, budgets, categories).
    •	ORM & DB: SQLAlchemy models mapped to a SQLite database (budget_app.db), created and seeded via API/create_db.py.
    •	Frontend: Static HTML pages (index.html, login.html, edit.html, visual.html) with CSS/JS that call your API using fetch.image.jpg
The UML you drew is implemented directly in API/models.py as tables and relationships.Updated_AGAIN_UML.drawio.jpg
Core data model

##All major features hang off the User table.Updated_AGAIN_UML.drawio.jpg
    •	User
    •	Fields: id, name, email, password_hash.
    •	Relationships: goals, budgets, recurring_payments, transactions (and optionally categories).
    •	Transaction
    •	Fields: id, date, amount (DECIMAL), description, is_income (bool), user_id, category_id.
    •	Relationships: user (who owns it), category (how it’s classified).
    •	This supports “earned vs spent”, current balance, and category based views.
    •	Category (the new module)
    •	Fields: id, name, type ("need", "want", "savings_debt"), is_default, and optionally user_id for custom categories.Updated_AGAIN_UML.drawio.jpg
    •	Relationships: transactions, budget_items (and optionally user).
    •	Default rows (Housing, Groceries, Dining Out, etc.) are seeded for everyone; custom categories can be created via the API.

##Budget & BudgetItem
    •	Budget: id, month, year, total_amt_planned, user_id.
    •	BudgetItem: id, planned_amt, budget_id, category_id.
    •	Design: one budget per user per month/year; many budget items, each tied to a category.Updated_AGAIN_UML.drawio.jpg
    •	Goal
    •	Fields: id, name, target_amount, current_amount, target_date, priority, user_id.
    •	Supports savings goals (big purchases, emergency fund, etc.).Updated_AGAIN_UML.drawio.jpg
    •	RecurringPayment & Reminder
    •	RecurringPayment: id, name, amount, due_day, start_date, end_date, frequency, is_active, user_id.
    •	Reminder: id, send_date, message, is_sent, recurring_payment_id.
    •	UML adds methods like generateNextOccurrence() and createUpcomingReminders() for future scheduling logic.Updated_AGAIN_UML.drawio.jpg

##Services & logic layer
The UML defines a service layer that will sit on top of the models.Updated_AGAIN_UML.drawio.jpg
    •	AuthService
    •	Methods: register(email, string, password), login(email, password), logout(user), changePassword(user, oldPassword, newPassword).
    •	Backed by the User model and your password hashing logic.
    •	FinanceCalculator
    •	Methods:
    •	calculateTotalIncome(user, start, end)
    •	calculateTotalExpenses(user, start, end)
    •	calculateNetBalance(user, start, end)
    •	estimateNextMonthBudget(user) returning a Budget.
    •	These functions use Transaction, Budget, and BudgetItem to implement “Total Money = Earned − Expense” and future estimates.HistoryUpdated_AGAIN_UML.drawio.jpg
    This gives you a clean separation: models handle persistence; services handle financial calculations and business rules.

##API design
    •	Database setup: API/create_db.py uses engine and Base from API/db.py to create_all() tables and then seed default categories.image.jpg
    •	DB access: API/db.py defines Sessionlocal and get_db() dependency for FastAPI routes.
    •	Category routes:
    •	GET /categories/ → return all categories as {id, name, type, is_default, (optional) user_id} for the frontend to populate dropdowns.
    •	POST /categories/ → accept JSON {name, type} and create a new category with is_default = False (and optional user_id if you wire auth).
    •	Other routes: similar patterns for transactions, budgets, login, etc., using Pydantic models to define request/response bodies.
    The frontend team calls these endpoints to list and create categories, then passes category_id back when creating transactions or budget items.
##Frontend interaction
    •	On page load, JS calls GET /categories/ and fills a <select> with all categories.
    •	When adding a transaction or budget item, the selected category_id is sent to the backend.
    •	For custom categories, a small form hit POST /categories/, then inserts the new option into the dropdown so the user can use it immediately.
