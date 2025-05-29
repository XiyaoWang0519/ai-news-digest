# AI News Digest

A Python-based news aggregation system that collects and stores the latest AI news from various sources, starting with OpenAI's official news feed.

## Features

- 🚀 **OpenAI News Collection**: Fetches latest news from OpenAI with dual-path approach (RSS + HTML fallback)
- 📊 **SQLite Storage**: Automatic deduplication and persistent storage
- 🧪 **Fully Tested**: Comprehensive test suite with pytest
- 🔄 **Robust Fallback**: RSS-first with HTML scraping fallback for reliability
- 📅 **Date Parsing**: Intelligent timestamp handling with timezone support

## Quick Start

### 1. Setup Environment

```bash
git clone <your-repo>
cd ai-news-digest

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Daily Collection

```bash
python run_daily.py
```

Expected output:
```
[OpenAI News] 571 items
Saved 571 items in total.
```

### 3. Query Recent News

```python
from digester.store import get_recent_items

# Get 10 most recent items
recent = get_recent_items(10)
for item in recent:
    print(f"{item['title']} - {item['published_at']}")
```

## Project Structure

```
ai-news-digest/
├── collectors/
│   ├── base.py              # Abstract base collector class
│   ├── openai_news.py       # OpenAI news collector (RSS + scraping)
│   └── google_ai_rss.py     # Google AI Blog collector (planned)
├── digester/
│   ├── store.py             # SQLite storage with deduplication
│   └── summariser.py        # AI summarization (planned)
├── tests/
│   ├── test_openai_news.py  # OpenAI collector tests
│   └── test_store.py        # Storage tests
├── templates/               # HTML templates (planned)
├── output/                  # Generated reports (planned)
├── requirements.txt         # Python dependencies
├── run_daily.py            # Main collection script
└── digest.sqlite3          # SQLite database (auto-created)
```

## Dependencies

Core libraries used:
- `requests` - HTTP requests
- `feedparser` - RSS feed parsing
- `beautifulsoup4` - HTML parsing fallback
- `python-dateutil` - Intelligent date parsing
- `pydantic` - Data validation (planned)
- `jinja2` - Template rendering (planned)

## OpenAI News Collector

The OpenAI collector uses a dual-path approach for maximum reliability:

1. **RSS Fast Path**: Tries official RSS feed first (`https://openai.com/news/rss.xml`)
2. **HTML Fallback**: Scrapes the news page if RSS fails or returns no items

### Example Usage

```python
from collectors.openai_news import OpenAINewsCollector

collector = OpenAINewsCollector()
items = collector.fetch_items()

print(f"Found {len(items)} items")
for item in items[:3]:
    print(f"- {item['title']}")
    print(f"  URL: {item['url']}")
    print(f"  Published: {item['published_at']}")
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run only OpenAI collector tests
python -m pytest tests/test_openai_news.py -v
```

## Database Schema

The SQLite database stores news items with the following schema:

```sql
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published_at TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Roadmap

- [ ] Google AI Blog collector
- [ ] Anthropic news collector  
- [ ] AI-powered summarization
- [ ] HTML report generation
- [ ] Email notifications
- [ ] Web dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `python -m pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
