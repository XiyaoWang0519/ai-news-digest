"""Tests for collectors.google_ai_rss module."""
import pytest
from collectors.google_ai_rss import GoogleAIRSCollector


class TestGoogleAIRSCollector:
    """Test the Google AI RSS collector stub."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = GoogleAIRSCollector()
    
    def test_source_name(self):
        """Test that source name is set correctly."""
        assert self.collector.source_name == "Google AI RSS"
    
    def test_fetch_items_returns_empty_list(self):
        """Test that fetch_items returns empty list (stub implementation)."""
        result = self.collector.fetch_items()
        assert result == []
        assert isinstance(result, list)
    
    def test_inherits_from_collector(self):
        """Test that GoogleAIRSCollector inherits from Collector base class."""
        from collectors.base import Collector
        assert isinstance(self.collector, Collector)
    
    def test_implements_abstract_method(self):
        """Test that the abstract fetch_items method is implemented."""
        # Should not raise TypeError for missing abstract method
        collector = GoogleAIRSCollector()
        assert hasattr(collector, 'fetch_items')
        assert callable(collector.fetch_items) 