"""Tests for collectors.base module."""
import pytest
from abc import ABC
from collectors.base import Collector


class TestCollector:
    """Test the abstract Collector base class."""
    
    def test_collector_is_abstract(self):
        """Test that Collector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Collector()
    
    def test_collector_requires_source_name_in_subclass(self):
        """Test that Collector requires source_name to be defined in subclasses."""
        # The base class doesn't define source_name, concrete implementations must
        assert not hasattr(Collector, 'source_name') or Collector.source_name is None
    
    def test_collector_has_fetch_items_method(self):
        """Test that Collector has abstract fetch_items method."""
        assert hasattr(Collector, 'fetch_items')
        assert Collector.fetch_items.__isabstractmethod__
    
    def test_concrete_implementation(self):
        """Test that a concrete implementation can be created."""
        class TestCollector(Collector):
            source_name = "Test Source"
            
            def fetch_items(self):
                return [{"title": "test", "url": "http://test.com", 
                        "published_at": "2025-01-01T00:00:00Z", "source": "test"}]
        
        collector = TestCollector()
        assert collector.source_name == "Test Source"
        items = collector.fetch_items()
        assert len(items) == 1
        assert items[0]["title"] == "test" 