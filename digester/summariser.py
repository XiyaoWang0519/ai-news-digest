"""
Structured daily digest powered by OpenRouter (Gemini-2.5-flash).
"""
from __future__ import annotations
import os, json, hashlib, logging, datetime, textwrap, requests
from typing import List, Dict, Any

import jsonschema
from bs4 import BeautifulSoup
from readability import Document
from dateutil import tz, parser as dp
from openai import OpenAI

# ------------------------------------------------------------------#
# OpenRouter setup
# ------------------------------------------------------------------#
MODEL = "google/gemini-2.5-flash-preview-05-20"
MAX_PER_DIGEST = int(os.getenv("MAX_STORIES", 8))
CHAR_LIMIT      = int(os.getenv("ARTICLE_CHAR_LIMIT", 5000))

# Jina.ai fallback endpoint
JINA_ENDPOINT = "https://r.jina.ai/"

# OpenRouter headers
OPENROUTER_HEADERS = {
    "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://example.com"),
    "X-Title": "AI-News-Digest"
}

log = logging.getLogger(__name__)

# ------------------------------------------------------------------#
# JSON schema for validation
# ------------------------------------------------------------------#
DIGEST_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["date", "executive_summary", "stories"],
    "properties": {
        "date": {"type": "string"},
        "executive_summary": {"type": "string"},
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "url",
                             "published_at", "source", "summary"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "published_at": {"type": "string"},
                    "source": {"type": "string"},
                    "category": {"type": "string"},
                    "summary": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    }
}

# ------------------------------------------------------------------#
# Public API
# ------------------------------------------------------------------#
def create_digest(items: List[Dict], date: datetime.date | None = None) -> Dict:
    """
    Given DB rows (title, url, published_at, source …) return structured digest dict.
    Saves token cost by:
      * limiting to MAX_PER_DIGEST newest items
      * scraping article body once, trimming to CHAR_LIMIT chars
      * building ONE chat completion with function-call JSON response
    """
    if not date:
        date = datetime.date.today()

    # 1 Filter & sort
    items = sorted(items, key=lambda x: x["published_at"], reverse=True)[:MAX_PER_DIGEST]

    # 2 Enrich each story with article text
    for it in items:
        # Use RSS description if available and substantial, otherwise scrape
        if it.get("description") and len(it["description"].strip()) > 50:
            it["content"] = it["description"][:CHAR_LIMIT]
            log.info("Using RSS description for %s", it["url"])
        else:
            it["content"] = _extract_text(it["url"])

    # 3 Build user prompt
    prompt = _build_prompt(items, str(date))

    # 4 Call Gemini-flash via OpenRouter using requests directly
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://example.com"),
        "X-Title": "AI-News-Digest"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system",
             "content": "You are an expert AI-news curator. "
                        "You MUST produce complete, valid JSON. "
                        "Do not truncate any fields or strings."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 4096,
        "temperature": 0.3
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()
    resp_data = response.json()

    # 5 Parse & validate
    try:
        response_content = resp_data["choices"][0]["message"]["content"]
        print(f"Response length: {len(response_content)} characters")
        print(f"Response tokens used: {resp_data.get('usage', {}).get('completion_tokens', 'unknown')}")
        
        digest = json.loads(response_content)
        jsonschema.validate(instance=digest, schema=DIGEST_SCHEMA)
        return digest
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response content length: {len(resp_data['choices'][0]['message']['content'])}")
        print(f"Last 200 chars: ...{resp_data['choices'][0]['message']['content'][-200:]}")
        
        # Try to identify if it's a truncation issue
        content = resp_data['choices'][0]['message']['content']
        if not content.rstrip().endswith('}'):
            print("❌ JSON appears to be truncated (doesn't end with })")
            print("💡 Try reducing MAX_STORIES or ARTICLE_CHAR_LIMIT")
        
        raise
    except KeyError as e:
        print(f"Response structure error: {e}")
        print(f"Full response keys: {resp_data.keys()}")
        if 'choices' in resp_data:
            print(f"Choices available: {len(resp_data['choices'])}")
        raise

# ------------------------------------------------------------------#
# Helpers
# ------------------------------------------------------------------#
def _extract_text(url: str) -> str:
    """Return main text, trying direct fetch then jina.ai fallback."""
    try:
        return _direct_readable(url)
    except requests.HTTPError as exc:
        if exc.response.status_code == 403:
            log.info("403 – trying jina.ai fallback for %s", url)
            return _jina_readable(url)
        raise
    except Exception as exc:
        log.warning("extract_text failed %s: %s", url, exc)
        return ""

def _direct_readable(url: str) -> str:
    r = requests.get(url, timeout=20,
                     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    r.raise_for_status()
    doc  = Document(r.text)
    soup = BeautifulSoup(doc.summary(), "html.parser")
    return soup.get_text(" ", strip=True)[:CHAR_LIMIT]

def _jina_readable(url: str) -> str:
    r = requests.get(JINA_ENDPOINT + url, timeout=20,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    text = r.text.strip()
    return text[:CHAR_LIMIT] if text else ""

def _build_prompt(items: List[Dict], date_str: str) -> str:
    bullet_blocks = []
    for it in items:
        body_short = textwrap.shorten(it["content"], 400, placeholder="…")  # Reduced from 700 to 400
        # Generate SHA256 ID for the URL
        url_id = hashlib.sha256(it['url'].encode('utf-8')).hexdigest()[:16]
        bullet_blocks.append(
            f"### STORY\n"
            f"Title: {it['title']}\n"
            f"Source: {it['source']}\n"
            f"URL: {it['url']}\n"
            f"ID: {url_id}\n"
            f"Published: {it['published_at']}\n"
            f"Article:\n{body_short}\n"
        )
    return (
        f"DATE: {date_str}\n\n"
        "You will produce a COMPLETE JSON object with the following structure.\n"
        "IMPORTANT: Ensure all strings are properly closed and the JSON is valid!\n\n"
        "{\n"
        '  "date": "' + date_str + '",\n'
        '  "executive_summary": "2-3 sentences summarizing the key AI developments today",\n'
        '  "stories": [\n'
        '    {\n'
        '      "id": "use the provided ID for each story",\n'
        '      "title": "original title",\n'
        '      "url": "original url",\n'
        '      "published_at": "original published date",\n'
        '      "source": "original source",\n'
        '      "category": "one of: product/research/policy/culture/misc",\n'
        '      "summary": "1-2 sentence summary of the story",\n'
        '      "tags": ["up to 3 relevant tags"]\n'  # Reduced from 4 to 3 tags
        '    }\n'
        '  ]\n'
        "}\n\n"
        "Stories:\n\n"
        + "\n".join(bullet_blocks)
    )
