# AI News Digest Summariser Setup

This guide helps you set up the structured JSON summariser that generates daily digests using OpenRouter and Gemini-2.5-flash.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```dotenv
# OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_REFERER=https://github.com/yourusername/ai-news-digest

# Summariser controls
MAX_STORIES=12          # cap per-digest
ARTICLE_CHAR_LIMIT=7000 # scrape limit to save tokens
```

### 3. Get OpenRouter API Key
1. Sign up at [OpenRouter.ai](https://openrouter.ai)
2. Go to Keys section and create a new API key
3. Add it to your `.env` file

## 🧪 Test the Summariser

Run the test script to see it in action:
```bash
python tests/test_summariser_live.py
```

This will:
- Pull the 10 most recent news items from your database
- Generate a structured digest with executive summary
- Print summaries for each story

## 📅 Generate Daily Digest

Run the full pipeline:
```bash
python run_daily.py
```

This will:
1. Collect new news items from configured sources
2. Save them to the database
3. Generate a daily digest using the summariser
4. Save the digest to `output/YYYY-MM-DD.json`

## 📁 Output Format

The generated JSON digest has this structure:
```json
{
  "date": "2025-01-29",
  "executive_summary": "Key AI developments summary...",
  "stories": [
    {
      "id": "abc123...",
      "title": "Story Title",
      "url": "https://...",
      "published_at": "2025-01-29T10:00:00Z",
      "source": "OpenAI News",
      "category": "product",
      "summary": "1-2 sentence story summary",
      "tags": ["ai", "product", "launch"]
    }
  ]
}
```

## 💰 Cost Optimization

The summariser is designed to be cost-effective:
- Limits articles to first 7,000 characters
- Shortens content to ~700 chars per story in prompts
- Uses one API call for the entire digest (not per-story)
- Uses Gemini-2.5-flash (one of the cheapest high-quality models)

## 🔧 Configuration

Environment variables you can adjust:

- `MAX_STORIES`: Maximum stories per digest (default: 12)
- `ARTICLE_CHAR_LIMIT`: Max characters to scrape per article (default: 7000)
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `OPENROUTER_REFERER`: Any URL you control (for OpenRouter's requirements)

## 🚨 Troubleshooting

**Error: "No module named 'openai'"**
- Run: `pip install -r requirements.txt`

**Error: "OPENROUTER_API_KEY not set"**
- Make sure you've created a `.env` file with your API key

**Error: "Invalid JSON response"**
- The model occasionally returns malformed JSON. The system will retry automatically.

**Error: "No items found for digest generation"**
- Run the collectors first to gather news items: `python run_daily.py`

## 🎯 Next Steps

Once this is working:
- Set up GitHub Actions for automated daily runs
- Create HTML email templates using the JSON output
- Add more news sources to collectors/
- Customize categories and tags based on your needs 