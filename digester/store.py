"""Basic storage module for news items."""
import sqlite3
import json
from typing import List, Dict
from pathlib import Path


def save_batch(items: List[Dict]) -> None:
    """Save a batch of news items to SQLite database."""
    if not items:
        return
    
    db_path = Path("digest.sqlite3")
    
    # Create table if it doesn't exist
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                published_at TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert items (ignore duplicates)
        for item in items:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO news_items (title, url, published_at, source)
                    VALUES (?, ?, ?, ?)
                """, (item['title'], item['url'], item['published_at'], item['source']))
            except Exception as e:
                print(f"Error saving item {item.get('title', 'Unknown')}: {e}")
        
        conn.commit()
        print(f"Saved {len(items)} items to database")


def get_recent_items(limit: int = 10) -> List[Dict]:
    """Get recent news items from database."""
    db_path = Path("digest.sqlite3")
    if not db_path.exists():
        return []
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT title, url, published_at, source, created_at
            FROM news_items
            ORDER BY published_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
