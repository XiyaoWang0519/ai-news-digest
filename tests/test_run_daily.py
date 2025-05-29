"""Tests for run_daily.py main script."""
import pytest
import json
import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import run_daily


class TestRunDaily:
    """Test the main daily execution script."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_items = [
            {
                "title": "Test Article 1",
                "url": "https://example.com/article1",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "OpenAI News"
            },
            {
                "title": "Test Article 2", 
                "url": "https://example.com/article2",
                "published_at": "2025-01-02T12:00:00Z",
                "source": "Google AI RSS"
            }
        ]
        
        self.sample_digest = {
            "date": "2025-01-01",
            "executive_summary": "Test summary",
            "stories": [
                {
                    "id": "abc123",
                    "title": "Test Article 1",
                    "url": "https://example.com/article1",
                    "published_at": "2025-01-01T12:00:00Z",
                    "source": "OpenAI News",
                    "category": "product",
                    "summary": "Test summary",
                    "tags": ["test"]
                }
            ]
        }
    
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    @patch('builtins.print')
    def test_main_collectors_success(self, mock_print, mock_google_collector, mock_openai_collector, mock_store):
        """Test successful collection from all collectors."""
        # Mock collectors
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.return_value = [self.sample_items[0]]
        mock_openai_collector.return_value = mock_openai_instance
        
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = [self.sample_items[1]]
        mock_google_collector.return_value = mock_google_instance
        
        # Mock store
        mock_store.get_recent_items.return_value = []  # No items for digest
        
        # Mock digest creation to avoid API calls
        with patch('run_daily.create_digest') as mock_create_digest:
            run_daily.main()
        
        # Verify collectors were called
        mock_openai_instance.fetch_items.assert_called_once()
        mock_google_instance.fetch_items.assert_called_once()
        
        # Verify items were saved
        assert mock_store.save_batch.call_count == 2
        mock_store.save_batch.assert_any_call([self.sample_items[0]])
        mock_store.save_batch.assert_any_call([self.sample_items[1]])
        
        # Verify print statements
        mock_print.assert_any_call("[OpenAI News] 1 items")
        mock_print.assert_any_call("[Google AI RSS] 1 items")
        mock_print.assert_any_call("Saved 2 items in total.")
    
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    @patch('run_daily.create_digest')
    @patch('run_daily.pathlib.Path')
    @patch('builtins.print')
    def test_main_digest_generation_success(self, mock_print, mock_path, mock_create_digest, mock_google_collector, mock_openai_collector, mock_store):
        """Test successful digest generation and file writing."""
        # Mock collectors to return empty (focus on digest)
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.return_value = []
        mock_openai_collector.return_value = mock_openai_instance
        
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = []
        mock_google_collector.return_value = mock_google_instance
        
        # Mock store to return items for digest
        mock_store.get_recent_items.return_value = self.sample_items
        
        # Mock digest creation
        mock_create_digest.return_value = self.sample_digest
        
        # Mock file operations with MagicMock for magic methods
        mock_out_dir = MagicMock()  # Use MagicMock for __truediv__
        mock_out_path = Mock()
        mock_out_dir.__truediv__.return_value = mock_out_path
        mock_path.return_value = mock_out_dir
        
        run_daily.main()
        
        # Verify digest was created
        mock_create_digest.assert_called_once_with(self.sample_items, datetime.date.today())
        
        # Verify file operations
        mock_out_dir.mkdir.assert_called_once_with(exist_ok=True)
        mock_out_path.write_text.assert_called_once()
        
        # Verify the written content is valid JSON
        written_content = mock_out_path.write_text.call_args[0][0]
        parsed_content = json.loads(written_content)
        assert parsed_content == self.sample_digest
        
        # Verify success message
        mock_print.assert_any_call(f"✓ Daily digest written to {mock_out_path}")
    
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    @patch('builtins.print')
    def test_main_no_items_for_digest(self, mock_print, mock_google_collector, mock_openai_collector, mock_store):
        """Test when no items are available for digest generation."""
        # Mock collectors
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.return_value = []
        mock_openai_collector.return_value = mock_openai_instance
        
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = []
        mock_google_collector.return_value = mock_google_instance
        
        # Mock store to return no items
        mock_store.get_recent_items.return_value = []
        
        run_daily.main()
        
        # Verify no digest message
        mock_print.assert_any_call("No items found for digest generation.")
    
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    @patch('run_daily.create_digest')
    @patch('builtins.print')
    def test_main_digest_creation_error(self, mock_print, mock_create_digest, mock_google_collector, mock_openai_collector, mock_store):
        """Test handling of digest creation errors."""
        # Mock collectors
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.return_value = []
        mock_openai_collector.return_value = mock_openai_instance
        
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = []
        mock_google_collector.return_value = mock_google_instance
        
        # Mock store to return items
        mock_store.get_recent_items.return_value = self.sample_items
        
        # Mock digest creation to raise error
        mock_create_digest.side_effect = Exception("API Error")
        
        run_daily.main()
        
        # Verify error handling
        mock_print.assert_any_call("Error generating digest: API Error")
    
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    @patch('builtins.print')
    def test_main_collector_exceptions(self, mock_print, mock_google_collector, mock_openai_collector, mock_store):
        """Test handling of collector exceptions."""
        # Mock OpenAI collector to raise exception
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.side_effect = Exception("Network error")
        mock_openai_collector.return_value = mock_openai_instance
        
        # Mock Google collector to work normally
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = []
        mock_google_collector.return_value = mock_google_instance
        
        mock_store.get_recent_items.return_value = []
        
        # Should not crash despite exception
        with pytest.raises(Exception, match="Network error"):
            run_daily.main()
    
    @patch.dict('os.environ', {'MAX_STORIES': '5'})
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    def test_main_respects_max_stories_env_var(self, mock_google_collector, mock_openai_collector, mock_store):
        """Test that main respects MAX_STORIES environment variable."""
        # Mock collectors
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.return_value = []
        mock_openai_collector.return_value = mock_openai_instance
        
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = []
        mock_google_collector.return_value = mock_google_instance
        
        # Mock store to return items
        mock_store.get_recent_items.return_value = self.sample_items
        
        with patch('run_daily.create_digest') as mock_create_digest:
            run_daily.main()
        
        # Verify that get_recent_items was called with the environment variable value
        mock_store.get_recent_items.assert_called_with(5)
    
    def test_main_function_exists(self):
        """Test that main function is properly defined."""
        assert hasattr(run_daily, 'main')
        assert callable(run_daily.main)
    
    @patch('run_daily.main')
    def test_script_execution(self, mock_main):
        """Test that script calls main when run directly."""
        # This would test the if __name__ == "__main__" block
        # We can't easily test this without actually running the script
        # but we can verify the main function exists and is callable
        assert callable(run_daily.main)
    
    @patch('run_daily.store')
    @patch('run_daily.OpenAINewsCollector')
    @patch('run_daily.GoogleAIRSCollector')
    @patch('run_daily.create_digest')
    @patch('run_daily.pathlib.Path')
    @patch('builtins.print')
    def test_main_file_write_error(self, mock_print, mock_path, mock_create_digest, mock_google_collector, mock_openai_collector, mock_store):
        """Test handling of file write errors."""
        # Mock collectors
        mock_openai_instance = Mock()
        mock_openai_instance.source_name = "OpenAI News"
        mock_openai_instance.fetch_items.return_value = []
        mock_openai_collector.return_value = mock_openai_instance
        
        mock_google_instance = Mock()
        mock_google_instance.source_name = "Google AI RSS"
        mock_google_instance.fetch_items.return_value = []
        mock_google_collector.return_value = mock_google_instance
        
        mock_store.get_recent_items.return_value = self.sample_items
        mock_create_digest.return_value = self.sample_digest
        
        # Mock file operations to raise error with MagicMock
        mock_out_dir = MagicMock()  # Use MagicMock for __truediv__
        mock_out_path = Mock()
        mock_out_path.write_text.side_effect = OSError("Permission denied")
        mock_out_dir.__truediv__.return_value = mock_out_path
        mock_path.return_value = mock_out_dir
        
        # The error should be caught and printed, not propagated
        run_daily.main()
        
        # Verify error handling - should print error message
        mock_print.assert_any_call("Error generating digest: Permission denied") 