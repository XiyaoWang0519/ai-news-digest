"""
Collector for https://openai.com/news
Tries the official RSS feed first (fast), then falls back to HTML scraping.
"""
from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timezone
import logging, hashlib

import requests, feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dp
from urllib.parse import urljoin

from .base import Collector

log = logging.getLogger(__name__)

class OpenAINewsCollector(Collector):
    source_name = "OpenAI News"
    RSS_CANDIDATES = [
        "https://openai.com/news/rss.xml",    # appears to exist again as of early 2025 
        "https://openrss.org/openai.com/news" # community mirror (fallback)
    ]
    PAGE_URL = "https://openai.com/news"

    def fetch_items(self) -> List[Dict]:
        # 1 Try RSS first (fast, no HTML parsing)
        for rss in self.RSS_CANDIDATES:
            items = self._try_rss(rss)
            if items:
                return items

        # 2 Fallback: scrape the News landing page
        return self._scrape_page()

    # ---------- helpers ----------
    def _try_rss(self, url: str) -> List[Dict]:
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                return []
            out = []
            for e in feed.entries:
                # Extract description/summary if available
                description = ""
                if hasattr(e, 'summary'):
                    description = e.summary
                elif hasattr(e, 'description'):
                    description = e.description
                
                out.append(
                    dict(
                        title        = e.title,
                        url          = e.link,
                        published_at = self._to_iso(e.published),
                        source       = self.source_name,
                        description  = description,  # Add RSS description as fallback content
                    )
                )
            log.info("OpenAI RSS ok via %s (%d items)", url, len(out))
            return out
        except Exception as exc:
            log.warning("RSS failed %s -> %s", url, exc)
            return []

    def _scrape_page(self) -> List[Dict]:
        resp = requests.get(self.PAGE_URL, timeout=20,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select("main a[href^='/']")
        items = []
        for a in cards:
            # Skip nav/duplicate links
            if not a.find("time"):
                continue
            title = a.get_text(" ", strip=True)
            link  = urljoin(self.PAGE_URL, a["href"])
            ts    = a.find("time").get("datetime") or a.find("time").text
            items.append(
                dict(
                    title        = title,
                    url          = link,
                    published_at = self._to_iso(ts),
                    source       = self.source_name,
                )
            )
        log.info("Scraped OpenAI page (%d items)", len(items))
        return items

    @staticmethod
    def _to_iso(ts: str) -> str:
        """Return UTC ISO-8601 string."""
        dt = dp.parse(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat() 