"""Tests for digester.store module."""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from digester import store


class TestStore:
    """Test the database storage functionality."""
    
    def setup_method(self):
        """Set up test fixtures with temporary database."""
        # Create a temporary database file for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.test_db_path = Path(self.temp_db.name)
        
        # Sample test data
        self.sample_items = [
            {
                "title": "Test Article 1",
                "url": "https://example.com/article1",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "Test Source"
            },
            {
                "title": "Test Article 2",
                "url": "https://example.com/article2",
                "published_at": "2025-01-02T12:00:00Z",
                "source": "Test Source"
            }
        ]
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove temporary database file
        if self.test_db_path.exists():
            self.test_db_path.unlink()
    
    def test_save_batch_empty_items(self):
        """Test saving empty list of items does nothing."""
        # Use actual Path but with a non-existent file
        test_path = Path("test_nonexistent.db")
        
        with patch('digester.store.Path') as mock_path:
            mock_path.return_value = test_path
            
            # Should return early and not create database
            store.save_batch([])
            
            # Database should not be created
            assert not test_path.exists()
    
    @patch('digester.store.Path')
    def test_save_batch_creates_table(self, mock_path):
        """Test that save_batch creates the news_items table."""
        mock_path.return_value = self.test_db_path
        
        store.save_batch(self.sample_items)
        
        # Check that database was created and table exists
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='news_items'
            """)
            assert cursor.fetchone() is not None
    
    @patch('digester.store.Path')
    def test_save_batch_inserts_items(self, mock_path):
        """Test that save_batch correctly inserts items."""
        mock_path.return_value = self.test_db_path
        
        store.save_batch(self.sample_items)
        
        # Check that items were inserted
        with sqlite3.connect(self.test_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM news_items ORDER BY id")
            rows = cursor.fetchall()
            
            assert len(rows) == 2
            assert rows[0]["title"] == "Test Article 1"
            assert rows[0]["url"] == "https://example.com/article1"
            assert rows[1]["title"] == "Test Article 2"
    
    @patch('digester.store.Path')
    def test_save_batch_ignores_duplicates(self, mock_path):
        """Test that save_batch ignores duplicate URLs."""
        mock_path.return_value = self.test_db_path
        
        # Save items first time
        store.save_batch(self.sample_items)
        
        # Save same items again (should be ignored)
        store.save_batch(self.sample_items)
        
        # Check that only 2 items exist (no duplicates)
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM news_items")
            count = cursor.fetchone()[0]
            assert count == 2
    
    @patch('digester.store.Path')
    @patch('builtins.print')
    def test_save_batch_handles_errors(self, mock_print, mock_path):
        """Test that save_batch handles database errors gracefully."""
        mock_path.return_value = self.test_db_path
        
        # Create items with missing required fields
        bad_items = [{"title": "Test", "url": "https://test.com"}]  # Missing published_at
        
        store.save_batch(bad_items)
        
        # Should have printed an error message (exact format may vary)
        # Check that an error was printed
        assert mock_print.call_count >= 1
        error_calls = [call for call in mock_print.call_args_list if 'Error saving item' in str(call)]
        assert len(error_calls) > 0
    
    @patch('digester.store.Path')
    def test_get_recent_items_no_database(self, mock_path):
        """Test get_recent_items when database doesn't exist."""
        mock_path.return_value = Path("nonexistent.db")
        
        result = store.get_recent_items()
        
        assert result == []
    
    @patch('digester.store.Path')
    def test_get_recent_items_empty_database(self, mock_path):
        """Test get_recent_items with empty database."""
        mock_path.return_value = self.test_db_path
        
        # Create empty database
        with sqlite3.connect(self.test_db_path) as conn:
            conn.execute("""
                CREATE TABLE news_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    published_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        result = store.get_recent_items()
        
        assert result == []
    
    @patch('digester.store.Path')
    def test_get_recent_items_with_data(self, mock_path):
        """Test get_recent_items with existing data."""
        mock_path.return_value = self.test_db_path
        
        # Save test data
        store.save_batch(self.sample_items)
        
        result = store.get_recent_items()
        
        assert len(result) == 2
        assert result[0]["title"] == "Test Article 2"  # Should be ordered by published_at DESC
        assert result[1]["title"] == "Test Article 1"
        assert "created_at" in result[0]  # Should include created_at field
    
    @patch('digester.store.Path')
    def test_get_recent_items_limit(self, mock_path):
        """Test get_recent_items respects limit parameter."""
        mock_path.return_value = self.test_db_path
        
        # Save test data
        store.save_batch(self.sample_items)
        
        result = store.get_recent_items(limit=1)
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Article 2"  # Most recent
    
    @patch('digester.store.Path')
    def test_table_schema(self, mock_path):
        """Test that the created table has the correct schema."""
        mock_path.return_value = self.test_db_path
        
        store.save_batch(self.sample_items)
        
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(news_items)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            expected_columns = {
                "id": "INTEGER",
                "title": "TEXT",
                "url": "TEXT",
                "published_at": "TEXT",
                "source": "TEXT",
                "created_at": "TIMESTAMP"
            }
            
            for col_name, col_type in expected_columns.items():
                assert col_name in columns
                assert columns[col_name] == col_type
    
    @patch('digester.store.Path')
    def test_url_unique_constraint(self, mock_path):
        """Test that URL has a unique constraint."""
        mock_path.return_value = self.test_db_path
        
        # Save first batch
        store.save_batch(self.sample_items)
        
        # Try to save item with duplicate URL but different title
        duplicate_url_item = [{
            "title": "Different Title",
            "url": "https://example.com/article1",  # Same URL as first item
            "published_at": "2025-01-03T12:00:00Z",
            "source": "Different Source"
        }]
        
        store.save_batch(duplicate_url_item)
        
        # Should still only have 2 items (duplicate ignored)
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM news_items")
            count = cursor.fetchone()[0]
            assert count == 2 