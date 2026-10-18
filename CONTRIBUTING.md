# Contributing to Language Agnostic Chatbot

Thank you for your interest in contributing!

## Code of Conduct
Please be polite, collaborative, and constructive when contributing issues or pull requests.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/language-agnostic-chatbot.git
   cd language-agnostic-chatbot
   ```

2. **Backend Setup**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   cp backend/.env.example backend/.env
   # Add your GROQ_API_KEY or GEMINI_API_KEY in backend/.env
   python backend/seed_documents/seed_odisha_schemes.py
   uvicorn backend.main:app --reload --port 8000
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Running Tests & Checks

Before submitting a Pull Request, ensure all checks pass:

```bash
# Run backend test suite
pytest

# Measure coverage
pytest --cov=backend

# Run security static analysis
bandit -r backend -ll -ii

# Lint backend
ruff check backend

# Verify frontend production build
cd frontend && npm run build
```

## Pull Request Guidelines
- Create a dedicated feature branch from `main`.
- Add unit or integration tests for new features and bug fixes.
- Follow PEP 8 style for Python and modern React conventions for frontend.
