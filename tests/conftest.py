"""Shared test fixtures and configuration."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def temp_db():
    """Provide a temporary database file for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield Path(temp_file.name)
    # Cleanup
    if Path(temp_file.name).exists():
        Path(temp_file.name).unlink()


@pytest.fixture
def sample_news_items():
    """Provide sample news items for testing."""
    return [
        {
            "title": "AI Research Breakthrough",
            "url": "https://example.com/ai-research",
            "published_at": "2025-01-01T12:00:00Z",
            "source": "AI Research News",
            "description": "Major breakthrough in AI research announced today."
        },
        {
            "title": "OpenAI Model Update",
            "url": "https://openai.com/news/model-update",
            "published_at": "2025-01-02T15:30:00Z",
            "source": "OpenAI News"
        },
        {
            "title": "Ethics in AI Development",
            "url": "https://ethics.ai/development",
            "published_at": "2025-01-03T09:45:00Z",
            "source": "AI Ethics Journal",
            "description": "New guidelines for ethical AI development released."
        }
    ]


@pytest.fixture
def sample_digest():
    """Provide a sample digest for testing."""
    return {
        "date": "2025-01-01",
        "executive_summary": "Major AI developments include research breakthroughs and ethical guidelines.",
        "stories": [
            {
                "id": "abc123def456",
                "title": "AI Research Breakthrough",
                "url": "https://example.com/ai-research",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "AI Research News",
                "category": "research",
                "summary": "Researchers announce significant breakthrough in AI capabilities.",
                "tags": ["ai", "research", "breakthrough", "machine-learning"]
            },
            {
                "id": "def456ghi789",
                "title": "Ethics in AI Development",
                "url": "https://ethics.ai/development",
                "published_at": "2025-01-03T09:45:00Z",
                "source": "AI Ethics Journal",
                "category": "policy",
                "summary": "New ethical guidelines aim to improve responsible AI development.",
                "tags": ["ethics", "ai", "guidelines", "development"]
            }
        ]
    }


@pytest.fixture
def mock_requests_response():
    """Provide a mock requests response."""
    response = Mock()
    response.status_code = 200
    response.text = "<html><body><p>Mock article content</p></body></html>"
    response.json.return_value = {"success": True}
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def clean_environment():
    """Provide a clean environment for testing."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Clear test-related environment variables
    test_vars = ['OPENROUTER_API_KEY', 'MAX_STORIES', 'ARTICLE_CHAR_LIMIT', 'OPENROUTER_REFERER']
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env) 