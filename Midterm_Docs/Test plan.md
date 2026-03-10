## Test Plan

The goal of testing for the Budget Tracker API is to ensure that all endpoints function correctly, data is stored and retrieved accurately, and the application handles invalid input or errors properly. Testing focuses on validating the functionality of user and transaction management features.

Testing was performed using manual API testing through Swagger UI and HTTP requests, allowing each endpoint to be executed and verified individually. The tests ensure that requests return the correct status codes, database operations work correctly, and responses contain the expected data.

The main components tested include:

User creation
Transaction creation
Transaction retrieval by user
Balance calculation
Error handling for invalid or missing data

## Tests Performed and Test Types
# Functional Testing
Functional testing was performed to verify that each API endpoint performs its intended operation.
#Tests included:
Creating a new user
Creating income transactions
Creating expense transactions
Retrieving transactions for a specific user
Calculating the user's balance
Expected results were verified through the returned JSON responses and database updates.
Integration Testing
Integration testing ensured that the API, database, and ORM (SQLAlchemy) work together correctly.

# Examples:
Creating a transaction correctly inserts data into the database.
Retrieving transactions returns records associated with the correct user.
Balance calculations correctly aggregate transaction values.

## API Endpoint Testing
Endpoints were tested using FastAPI's Swagger UI (/docs) interface.

# Example endpoints tested/Method	Purpose:
POST   /user/login                         | Logs a user in
POST   /user/create_user                   | Creates a new user
GET    /transaction/balance                | Gets a balance from a user
POST   /transaction/add_transaction        | Creates a transaction
GET    /transaction/user_id                | Gets all transactions from a user
GET    /transaction/user_id/type/is_income | Finds a specific transaction based on paramaters
DELETE /transaction/user_id/transaction_id | Deletes a specific transaction

Each endpoint was tested with valid and invalid inputs to confirm correct behavior.

## Analysis Report

Testing confirmed that the API successfully handles core functionality including user creation, transaction storage, and balance calculations. The database integration with SQLite and SQLAlchemy performed reliably, with data correctly inserted and retrieved through API endpoints.

Errors encountered during development included issues with database schema mismatches and incorrect query parameters. These issues were resolved by updating the database schema and correcting route definitions.

Overall, the application meets its functional requirements and provides reliable API endpoints for managing user financial transactions.
