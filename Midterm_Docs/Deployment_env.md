##Deployment Environment

The Budget Tracker application is deployed as a RESTful API built with FastAPI and served using the Uvicorn ASGI server. The backend runs on Python 3.11 within a virtual environment created using Python’s venv module.

The application uses SQLite as its database, with the database stored locally in the project as budget_app.db. Database interactions are handled through SQLAlchemy ORM, which manages models and queries between the API and the database.

The system can be deployed on any environment that supports Python applications, including local development machines or cloud-based platforms such as AWS, Render, or Railway.

To run the application, the deployment environment must have the required Python dependencies installed. The API server can be started with the following command:

uvicorn API.main:app --reload

Once running, the API is accessible through HTTP endpoints and provides interactive documentation through Swagger UI at:

http://localhost:8000/docs

This deployment setup allows the backend service to process requests, manage transaction data, and interact with the SQLite database in a lightweight and portable environment.
