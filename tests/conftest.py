import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models.database import create_tables, seed_demo_users

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Session-level test fixture that runs automatically before any tests execute.
    Ensures that database tables and baseline demo users exist across all test runs
    regardless of test execution order or CI environment.
    """
    create_tables()
    seed_demo_users()
