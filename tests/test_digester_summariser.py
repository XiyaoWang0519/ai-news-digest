"""Tests for digester.summariser module."""
import pytest
import json
import os
import datetime
from unittest.mock import Mock, patch, MagicMock
from digester import summariser


class TestSummariser:
    """Test the AI summarisation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_items = [
            {
                "title": "OpenAI Releases GPT-5",
                "url": "https://openai.com/news/gpt5",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "OpenAI News",
                "description": "OpenAI has announced the release of GPT-5..."
            },
            {
                "title": "Anthropic Updates Claude",
                "url": "https://anthropic.com/news/claude-update",
                "published_at": "2025-01-02T12:00:00Z",
                "source": "Anthropic News"
            }
        ]
        
        self.mock_digest_response = {
            "date": "2025-01-01",
            "executive_summary": "Major AI developments this week include GPT-5 release and Claude updates.",
            "stories": [
                {
                    "id": "abc123",
                    "title": "OpenAI Releases GPT-5",
                    "url": "https://openai.com/news/gpt5",
                    "published_at": "2025-01-01T12:00:00Z",
                    "source": "OpenAI News",
                    "category": "product",
                    "summary": "OpenAI announced GPT-5 with improved capabilities.",
                    "tags": ["openai", "gpt-5", "language-model"]
                }
            ]
        }
    
    def test_constants(self):
        """Test that constants are properly defined."""
        assert summariser.MODEL == "google/gemini-2.5-flash-preview-05-20"
        assert summariser.MAX_PER_DIGEST == int(os.getenv("MAX_STORIES", 12))
        assert summariser.CHAR_LIMIT == int(os.getenv("ARTICLE_CHAR_LIMIT", 7000))
        assert summariser.JINA_ENDPOINT == "https://r.jina.ai/"
    
    def test_digest_schema_validation(self):
        """Test that the digest schema is valid."""
        # Valid digest should pass
        from jsonschema import validate
        validate(instance=self.mock_digest_response, schema=summariser.DIGEST_SCHEMA)
        
        # Invalid digest should fail
        invalid_digest = {"date": "2025-01-01"}  # Missing required fields
        with pytest.raises(Exception):
            validate(instance=invalid_digest, schema=summariser.DIGEST_SCHEMA)
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch('digester.summariser.requests')
    @patch('digester.summariser._extract_text')
    def test_create_digest_success(self, mock_extract_text, mock_requests):
        """Test successful digest creation."""
        # Mock text extraction
        mock_extract_text.return_value = "Extracted article content..."
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(self.mock_digest_response)}}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        result = summariser.create_digest(self.sample_items)
        
        assert result == self.mock_digest_response
        # Both items trigger text extraction: first has description but not substantial enough, second has none
        assert mock_extract_text.call_count == 2  # Both items need extraction
        mock_requests.post.assert_called_once()
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch('digester.summariser.requests')
    @patch('digester.summariser._extract_text')
    def test_create_digest_uses_rss_description(self, mock_extract_text, mock_requests):
        """Test that RSS descriptions are used when available."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(self.mock_digest_response)}}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        # Item with substantial description should not trigger text extraction
        items_with_description = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "Test Source",
                "description": "This is a substantial description with more than 50 characters that should be used instead of extracting text."
            }
        ]
        
        summariser.create_digest(items_with_description)
        
        # Should not call extract_text since description is substantial
        mock_extract_text.assert_not_called()
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch('digester.summariser.requests')
    @patch('digester.summariser._extract_text')
    def test_create_digest_limits_items(self, mock_extract_text, mock_requests):
        """Test that create_digest limits items to MAX_PER_DIGEST."""
        # Create more items than the limit
        many_items = []
        for i in range(20):  # More than MAX_PER_DIGEST (12)
            many_items.append({
                "title": f"Article {i}",
                "url": f"https://example.com/article{i}",
                "published_at": f"2025-01-{i+1:02d}T12:00:00Z",
                "source": "Test Source"
            })
        
        mock_extract_text.return_value = "Content"
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(self.mock_digest_response)}}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        summariser.create_digest(many_items)
        
        # Should only extract text for MAX_PER_DIGEST items
        assert mock_extract_text.call_count <= summariser.MAX_PER_DIGEST
    
    @patch('digester.summariser._extract_text')
    def test_create_digest_no_api_key(self, mock_extract_text):
        """Test that create_digest raises error when API key is missing."""
        # Mock extract_text to avoid actual web requests
        mock_extract_text.return_value = "test content"
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
                summariser.create_digest(self.sample_items)
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch('digester.summariser.requests')
    @patch('digester.summariser._extract_text')
    def test_create_digest_invalid_json_response(self, mock_extract_text, mock_requests):
        """Test handling of invalid JSON response."""
        mock_extract_text.return_value = "test content"
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "invalid json"}}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        with pytest.raises(json.JSONDecodeError):
            summariser.create_digest(self.sample_items)
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch('digester.summariser.requests')
    @patch('digester.summariser._extract_text')
    def test_create_digest_schema_validation_error(self, mock_extract_text, mock_requests):
        """Test handling of response that doesn't match schema."""
        mock_extract_text.return_value = "test content"
        invalid_response = {"date": "2025-01-01"}  # Missing required fields
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(invalid_response)}}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        with pytest.raises(Exception):  # jsonschema.ValidationError
            summariser.create_digest(self.sample_items)
    
    @patch('digester.summariser.requests')
    def test_direct_readable_success(self, mock_requests):
        """Test successful direct text extraction."""
        mock_response = Mock()
        mock_response.text = "<html><body><p>Article content</p></body></html>"
        mock_requests.get.return_value = mock_response
        
        with patch('digester.summariser.Document') as mock_doc_class:
            mock_doc = Mock()
            mock_doc.summary.return_value = "<p>Article content</p>"
            mock_doc_class.return_value = mock_doc
            
            result = summariser._direct_readable("https://example.com")
            
            assert "Article content" in result
            mock_requests.get.assert_called_once()
    
    @patch('digester.summariser.requests')
    def test_jina_readable_success(self, mock_requests):
        """Test successful Jina.ai text extraction."""
        mock_response = Mock()
        mock_response.text = "Clean article text from Jina"
        mock_requests.get.return_value = mock_response
        
        result = summariser._jina_readable("https://example.com")
        
        assert result == "Clean article text from Jina"
        mock_requests.get.assert_called_with(
            "https://r.jina.ai/https://example.com",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )
    
    @patch('digester.summariser._direct_readable')
    def test_extract_text_direct_success(self, mock_direct):
        """Test extract_text when direct method succeeds."""
        mock_direct.return_value = "Direct extraction content"
        
        result = summariser._extract_text("https://example.com")
        
        assert result == "Direct extraction content"
        mock_direct.assert_called_once_with("https://example.com")
    
    @patch('digester.summariser._direct_readable')
    @patch('digester.summariser._jina_readable')
    def test_extract_text_403_fallback(self, mock_jina, mock_direct):
        """Test extract_text falls back to Jina on 403 error."""
        # Import HTTPError from requests
        from requests.exceptions import HTTPError
        
        # Mock 403 error
        mock_response = Mock()
        mock_response.status_code = 403
        http_error = HTTPError()
        http_error.response = mock_response
        mock_direct.side_effect = http_error
        
        mock_jina.return_value = "Jina fallback content"
        
        result = summariser._extract_text("https://example.com")
        
        assert result == "Jina fallback content"
        mock_direct.assert_called_once()
        mock_jina.assert_called_once_with("https://example.com")
    
    @patch('digester.summariser._direct_readable')
    @patch('digester.summariser._jina_readable')
    def test_extract_text_other_error_propagates(self, mock_jina, mock_direct):
        """Test extract_text handles non-403 errors by returning empty string."""
        mock_direct.side_effect = Exception("Network error")
        
        # The function actually catches all exceptions and returns empty string
        result = summariser._extract_text("https://example.com")
        assert result == ""
        
        mock_jina.assert_not_called()
    
    @patch('digester.summariser._direct_readable')
    def test_extract_text_handles_general_exception(self, mock_direct):
        """Test extract_text handles general exceptions gracefully."""
        mock_direct.side_effect = Exception("General error")
        
        result = summariser._extract_text("https://example.com")
        
        assert result == ""
    
    def test_build_prompt(self):
        """Test prompt building."""
        items_with_content = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "Test Source",
                "content": "Article content here..."
            }
        ]
        
        result = summariser._build_prompt(items_with_content, "2025-01-01")
        
        assert "DATE: 2025-01-01" in result
        assert "Test Article" in result
        assert "https://example.com/test" in result
        assert "Article content here..." in result
        assert "JSON object" in result
    
    def test_build_prompt_generates_url_id(self):
        """Test that build_prompt generates SHA256 ID for URLs."""
        items_with_content = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "Test Source",
                "content": "Article content"
            }
        ]
        
        result = summariser._build_prompt(items_with_content, "2025-01-01")
        
        # Should contain a 16-character hex ID
        import re
        id_match = re.search(r"ID: ([a-f0-9]{16})", result)
        assert id_match is not None
    
    def test_build_prompt_truncates_long_content(self):
        """Test that build_prompt truncates very long content."""
        long_content = "A" * 1000  # Very long content
        items_with_content = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "published_at": "2025-01-01T12:00:00Z",
                "source": "Test Source",
                "content": long_content
            }
        ]
        
        result = summariser._build_prompt(items_with_content, "2025-01-01")
        
        # Content should be truncated (textwrap.shorten with 700 char limit)
        assert len(result) < len(long_content) + 500  # Much shorter than original
        assert "…" in result  # Should contain ellipsis
    
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"})
    @patch('digester.summariser.requests')
    @patch('digester.summariser._extract_text')
    def test_create_digest_with_date(self, mock_extract_text, mock_requests):
        """Test create_digest with specific date."""
        mock_extract_text.return_value = "Content"
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(self.mock_digest_response)}}
            ]
        }
        mock_requests.post.return_value = mock_response
        
        test_date = datetime.date(2025, 6, 15)
        summariser.create_digest(self.sample_items, date=test_date)
        
        # Check that the date was passed to the API call
        call_args = mock_requests.post.call_args
        payload = call_args[1]['json']
        prompt = payload['messages'][1]['content']
        assert "DATE: 2025-06-15" in prompt 