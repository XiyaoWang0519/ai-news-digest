# AI News Digest - Test Suite

This directory contains comprehensive tests for the AI News Digest application. The test suite covers all major components and provides excellent code coverage.

## Test Overview

The test suite includes **59 tests** covering the following modules:

### 📰 Collectors (`collectors/`)
- **Base Collector** (`test_collectors_base.py`) - 4 tests
  - Abstract class behavior
  - Interface requirements
  - Concrete implementation validation

- **OpenAI News Collector** (`test_collectors_openai_news.py`) - 17 tests
  - RSS feed parsing (success, failure, empty feeds)
  - HTML scraping fallback
  - Date/time parsing and conversion
  - Error handling and recovery
  - Content description handling

- **Google AI RSS Collector** (`test_collectors_google_ai_rss.py`) - 4 tests
  - Stub implementation validation
  - Base class inheritance

### 🗄️ Database Storage (`digester/store.py`)
- **Store Module** (`test_digester_store.py`) - 11 tests
  - Database creation and table schema
  - Item insertion and duplicate handling
  - Error handling for malformed data
  - Retrieval with ordering and limits
  - Unique constraints

### 🤖 AI Summarization (`digester/summariser.py`)
- **Summariser Module** (`test_digester_summariser.py`) - 18 tests
  - API integration with OpenRouter/Gemini
  - Text extraction (direct and Jina.ai fallback)
  - JSON schema validation
  - Error handling (network, API, parsing)
  - Content processing and truncation
  - Environment variable handling

### 🏃 Main Script (`run_daily.py`)
- **Main Execution** (`test_run_daily.py`) - 9 tests
  - Collector orchestration
  - Digest generation workflow
  - File output handling
  - Error recovery and reporting
  - Environment variable respect

## Running Tests

### Prerequisites
Make sure you have the virtual environment activated:
```bash
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with short traceback format
pytest --tb=short

# Run specific test file
pytest tests/test_collectors_openai_news.py

# Run specific test class
pytest tests/test_collectors_openai_news.py::TestOpenAINewsCollector

# Run specific test method
pytest tests/test_collectors_openai_news.py::TestOpenAINewsCollector::test_source_name
```

### Advanced Test Options
```bash
# Show test coverage
pytest --cov=collectors --cov=digester --cov-report=html

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Run tests matching pattern
pytest -k "test_rss"

# Stop on first failure
pytest -x
```

## Test Configuration

The test suite is configured via:
- `pytest.ini` - Main pytest configuration
- `tests/conftest.py` - Shared fixtures and setup

### Key Fixtures Available
- `temp_db` - Temporary database for testing storage
- `sample_news_items` - Sample news items data
- `sample_digest` - Sample digest structure
- `mock_requests_response` - Mock HTTP responses
- `clean_environment` - Clean environment variables

## Test Structure

### Mocking Strategy
The tests extensively use Python's `unittest.mock` to:
- Mock external API calls (OpenRouter, RSS feeds, web scraping)
- Mock file system operations
- Mock database operations with temporary files
- Mock environment variables

### Test Categories
1. **Unit Tests** - Test individual functions and methods
2. **Integration Tests** - Test component interactions
3. **Error Handling Tests** - Test failure scenarios
4. **Configuration Tests** - Test environment variable handling

## Coverage Areas

### ✅ What's Tested
- ✅ Data collection from RSS feeds and web scraping
- ✅ Database storage and retrieval
- ✅ AI-powered summarization
- ✅ Error handling and recovery
- ✅ File I/O operations
- ✅ Environment configuration
- ✅ JSON schema validation
- ✅ Date/time processing
- ✅ Text extraction and processing

### 🔄 Mock Usage
- 🔄 HTTP requests (no actual network calls)
- 🔄 OpenRouter API calls (no actual AI API usage)
- 🔄 File system operations (temporary files only)
- 🔄 External dependencies (feedparser, BeautifulSoup, etc.)

## Development Workflow

### Adding New Tests
1. Create test file following naming convention: `test_<module_name>.py`
2. Import the module under test
3. Use appropriate fixtures from `conftest.py`
4. Follow existing patterns for mocking
5. Add docstrings describing what each test validates

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ModuleName>`
- Test methods: `test_<functionality_being_tested>`

### Mocking Guidelines
- Mock external dependencies (network, filesystem, APIs)
- Use `patch` decorators for temporary mocking
- Use `Mock` and `MagicMock` for object mocking
- Mock at the appropriate level (function vs module)

## Continuous Integration

The test suite is designed to run in CI/CD environments:
- No external dependencies required
- All network calls mocked
- Temporary files cleaned up automatically
- Environment variables isolated

## Troubleshooting

### Common Issues
1. **Import Errors** - Ensure virtual environment is activated
2. **Test Failures** - Check mock setup and expectations
3. **Slow Tests** - Verify external calls are properly mocked
4. **Database Issues** - Temporary files should auto-cleanup

### Debug Mode
```bash
# Run with Python debugger on failure
pytest --pdb

# Print statements in tests
pytest -s

# More verbose output
pytest -vv
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Aim for good test coverage of new code
4. Update this README if adding new test categories

---

**Test Statistics**: 59 tests across 5 modules with comprehensive mocking and error handling coverage. 