# Language Agnostic Chatbot

This project contains the backend for the Language Agnostic Chatbot, built with FastAPI, LangChain, ChromaDB, and PostgreSQL.

## How to run

1. Install Docker and Docker Compose.
2. In the project root directory, run:
   ```bash
   docker-compose up --build
   ```
3. The backend API will be available at `http://localhost:8000`.
4. The API documentation (Swagger) is available at `http://localhost:8000/docs`.

### Demo Users
The system is seeded with the following demo users:
- **Student**: `student@demo.com` / `demo123`
- **Admin**: `admin@demo.com` / `admin123`

### Local Development
To run locally without Docker:
1. Ensure PostgreSQL is running.
2. Go to the `backend` directory.
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `uvicorn backend.main:app --reload`
