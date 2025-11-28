"""
VALORA Backend Test Configuration
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch
import os

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["GROQ_API_KEY"] = "test-groq-key"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mock_db():
    """Create a mock database connection."""
    with patch("app.db.session.get_db") as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture(scope="session")
def mock_redis():
    """Create a mock Redis connection."""
    with patch("app.core.cache.redis_client") as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        yield mock


@pytest.fixture(scope="session")
def mock_groq():
    """Create a mock Groq client."""
    with patch("groq.Groq") as mock:
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Mock AI response for testing"))
        ]
        mock.return_value.chat.completions.create.return_value = mock_response
        yield mock


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return {
        "id": "user_test_001",
        "email": "test@valora.ai",
        "name": "Test User",
        "organization": "Test Org",
        "role": "admin"
    }


@pytest.fixture
def sample_token(sample_user):
    """Create a sample JWT token."""
    from app.core.security import create_access_token
    
    return create_access_token(data={"sub": sample_user["email"]})


@pytest.fixture
def auth_headers(sample_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {sample_token}"}
