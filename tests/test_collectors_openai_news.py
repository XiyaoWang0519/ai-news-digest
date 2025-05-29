"""Tests for collectors.openai_news module."""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timezone
from collectors.openai_news import OpenAINewsCollector


class TestOpenAINewsCollector:
    """Test the OpenAI news collector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = OpenAINewsCollector()
    
    def test_source_name(self):
        """Test that source name is set correctly."""
        assert self.collector.source_name == "OpenAI News"
    
    def test_rss_candidates(self):
        """Test that RSS candidates are defined."""
        assert len(self.collector.RSS_CANDIDATES) >= 2
        assert "openai.com" in self.collector.RSS_CANDIDATES[0]
    
    @patch('collectors.openai_news.feedparser')
    def test_try_rss_success(self, mock_feedparser):
        """Test successful RSS parsing."""
        # Mock feedparser response
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.link = "https://openai.com/news/test"
        mock_entry.published = "2025-01-01T12:00:00Z"
        mock_entry.summary = "Test summary"
        
        mock_feed = Mock()
        mock_feed.entries = [mock_entry]
        mock_feedparser.parse.return_value = mock_feed
        
        result = self.collector._try_rss("https://test.com/rss")
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Article"
        assert result[0]["url"] == "https://openai.com/news/test"
        assert result[0]["source"] == "OpenAI News"
        assert result[0]["description"] == "Test summary"
    
    @patch('collectors.openai_news.feedparser')
    def test_try_rss_empty_feed(self, mock_feedparser):
        """Test RSS parsing with empty feed."""
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feedparser.parse.return_value = mock_feed
        
        result = self.collector._try_rss("https://test.com/rss")
        
        assert result == []
    
    @patch('collectors.openai_news.feedparser')
    def test_try_rss_exception(self, mock_feedparser):
        """Test RSS parsing with exception."""
        mock_feedparser.parse.side_effect = Exception("Network error")
        
        result = self.collector._try_rss("https://test.com/rss")
        
        assert result == []
    
    @patch('collectors.openai_news.requests')
    @patch('collectors.openai_news.BeautifulSoup')
    def test_scrape_page_success(self, mock_soup, mock_requests):
        """Test successful page scraping."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_requests.get.return_value = mock_response
        
        # Mock BeautifulSoup
        mock_time = Mock()
        mock_time.get.return_value = "2025-01-01T12:00:00Z"
        mock_time.text = "2025-01-01T12:00:00Z"
        
        mock_link = MagicMock()  # Use MagicMock for magic methods
        mock_link.get_text.return_value = "Test Article Title"
        mock_link.__getitem__.return_value = "/news/test-article"  # Now this will work
        mock_link.find.return_value = mock_time
        
        mock_soup_instance = Mock()
        mock_soup_instance.select.return_value = [mock_link]
        mock_soup.return_value = mock_soup_instance
        
        result = self.collector._scrape_page()
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Article Title"
        assert result[0]["url"] == "https://openai.com/news/test-article"
        assert result[0]["source"] == "OpenAI News"
    
    @patch('collectors.openai_news.requests')
    @patch('collectors.openai_news.BeautifulSoup')
    def test_scrape_page_no_time_elements(self, mock_soup, mock_requests):
        """Test page scraping with no time elements (should be skipped)."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_requests.get.return_value = mock_response
        
        # Mock BeautifulSoup with link that has no time element
        mock_link = Mock()
        mock_link.find.return_value = None  # No time element
        
        mock_soup_instance = Mock()
        mock_soup_instance.select.return_value = [mock_link]
        mock_soup.return_value = mock_soup_instance
        
        result = self.collector._scrape_page()
        
        assert result == []
    
    def test_to_iso_with_timezone(self):
        """Test ISO conversion with timezone."""
        ts = "2025-01-01T12:00:00+05:00"
        result = self.collector._to_iso(ts)
        # The method returns "+00:00" format, not "Z" format
        assert result.endswith("+00:00")  # Should be converted to UTC
        assert "07:00:00" in result  # 12:00 - 5 hours = 07:00 UTC
    
    def test_to_iso_without_timezone(self):
        """Test ISO conversion without timezone (assumes UTC)."""
        ts = "2025-01-01T12:00:00"
        result = self.collector._to_iso(ts)
        # The method returns "+00:00" format, not "Z" format
        assert result.endswith("+00:00")  # Should be converted to UTC
        assert "12:00:00" in result  # Should remain the same time
    
    @patch.object(OpenAINewsCollector, '_try_rss')
    def test_fetch_items_rss_success(self, mock_try_rss):
        """Test fetch_items when RSS succeeds."""
        expected_items = [{"title": "Test", "url": "http://test.com", 
                          "published_at": "2025-01-01T00:00:00Z", "source": "OpenAI News"}]
        mock_try_rss.return_value = expected_items
        
        result = self.collector.fetch_items()
        
        assert result == expected_items
        assert mock_try_rss.call_count == 1  # Should stop after first success
    
    @patch.object(OpenAINewsCollector, '_try_rss')
    @patch.object(OpenAINewsCollector, '_scrape_page')
    def test_fetch_items_rss_fails_scrape_fallback(self, mock_scrape, mock_try_rss):
        """Test fetch_items when RSS fails and falls back to scraping."""
        mock_try_rss.return_value = []  # RSS fails
        expected_items = [{"title": "Scraped", "url": "http://scraped.com", 
                          "published_at": "2025-01-01T00:00:00Z", "source": "OpenAI News"}]
        mock_scrape.return_value = expected_items
        
        result = self.collector.fetch_items()
        
        assert result == expected_items
        assert mock_try_rss.call_count == len(self.collector.RSS_CANDIDATES)  # Should try all RSS feeds
        mock_scrape.assert_called_once()
    
    @patch('collectors.openai_news.feedparser')
    def test_try_rss_with_description_fallback(self, mock_feedparser):
        """Test RSS parsing with description instead of summary."""
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.link = "https://openai.com/news/test"
        mock_entry.published = "2025-01-01T12:00:00Z"
        mock_entry.description = "Test description"
        
        # Mock hasattr to return False for summary, True for description
        with patch('builtins.hasattr') as mock_hasattr:
            def hasattr_side_effect(obj, attr):
                if attr == 'summary':
                    return False
                elif attr == 'description':
                    return True
                return True  # Default for other attributes
            mock_hasattr.side_effect = hasattr_side_effect
            
            mock_feed = Mock()
            mock_feed.entries = [mock_entry]
            mock_feedparser.parse.return_value = mock_feed
            
            result = self.collector._try_rss("https://test.com/rss")
            
            assert len(result) == 1
            assert result[0]["description"] == "Test description"
    
    @patch('collectors.openai_news.feedparser')
    def test_try_rss_no_description(self, mock_feedparser):
        """Test RSS parsing with no description or summary."""
        mock_entry = Mock()
        mock_entry.title = "Test Article"
        mock_entry.link = "https://openai.com/news/test"
        mock_entry.published = "2025-01-01T12:00:00Z"
        
        # Mock hasattr to return False for both summary and description
        with patch('builtins.hasattr') as mock_hasattr:
            def hasattr_side_effect(obj, attr):
                if attr in ['summary', 'description']:
                    return False
                return True  # Default for other attributes
            mock_hasattr.side_effect = hasattr_side_effect
            
            mock_feed = Mock()
            mock_feed.entries = [mock_entry]
            mock_feedparser.parse.return_value = mock_feed
            
            result = self.collector._try_rss("https://test.com/rss")
            
            assert len(result) == 1
            assert result[0]["description"] == "" 