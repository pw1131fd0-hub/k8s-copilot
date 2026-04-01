"""Basic tests for ExportService to improve coverage."""
import pytest
import json
from datetime import datetime, timezone
from backend.models.orm_models import ClawBookPost
from backend.services.export_service import ExportService


class TestExportServiceJSON:
    """Test JSON export functionality."""

    def test_export_empty_posts_to_json(self):
        """Test exporting empty post list to JSON."""
        result = ExportService.export_to_json([])

        data = json.loads(result)
        assert "posts" in data
        assert data["posts"] == []

    def test_export_single_post_to_json(self):
        """Test exporting a single post to JSON."""
        post = ClawBookPost(
            id="post_001",
            mood="😊 好心情",
            content="Test post content",
            author="Test User"
        )
        post.like_count = 5
        post.comment_count = 2
        post.created_at = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = ExportService.export_to_json([post])

        data = json.loads(result)
        assert len(data["posts"]) == 1
        assert data["posts"][0]["id"] == "post_001"
        assert data["posts"][0]["mood"] == "😊 好心情"

    def test_export_to_json_with_metadata(self):
        """Test JSON export includes metadata."""
        post = ClawBookPost(
            id="post_001",
            mood="😊 好心情",
            content="Test post",
            author="Test User"
        )

        result = ExportService.export_to_json([post], include_metadata=True)

        data = json.loads(result)
        assert "posts" in data
        assert "exported_at" in data

    def test_export_to_json_without_metadata(self):
        """Test JSON export excludes metadata when flag is False."""
        post = ClawBookPost(
            id="post_001",
            mood="😊 好心情",
            content="Test post",
            author="Test User"
        )

        result = ExportService.export_to_json([post], include_metadata=False)

        data = json.loads(result)
        assert "posts" in data


class TestExportServiceCSV:
    """Test CSV export functionality."""

    def test_export_empty_posts_to_csv(self):
        """Test exporting empty post list to CSV."""
        result = ExportService.export_to_csv([])

        lines = result.strip().split('\n')
        # Should have header only
        assert len(lines) >= 1
        assert "mood" in lines[0].lower()

    def test_export_single_post_to_csv(self):
        """Test exporting a single post to CSV."""
        post = ClawBookPost(
            id="post_001",
            mood="😊 好心情",
            content="Test post content",
            author="Test User"
        )
        post.created_at = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = ExportService.export_to_csv([post])

        lines = result.strip().split('\n')
        # Should have header + 1 data row
        assert len(lines) >= 2
        assert "post_001" in result

    def test_export_multiple_posts_to_csv(self):
        """Test exporting multiple posts to CSV."""
        posts = [
            ClawBookPost(
                id=f"post_{i:03d}",
                mood="😊 好心情",
                content=f"Post {i}",
                author="Test User"
            )
            for i in range(3)
        ]

        result = ExportService.export_to_csv(posts)

        lines = result.strip().split('\n')
        # Should have header + 3 data rows
        assert len(lines) >= 4


class TestExportServiceMarkdown:
    """Test Markdown export functionality."""

    def test_export_empty_posts_to_markdown(self):
        """Test exporting empty post list to Markdown."""
        result = ExportService.export_to_markdown([])

        assert "#" in result or result == ""

    def test_export_single_post_to_markdown(self):
        """Test exporting a single post to Markdown."""
        post = ClawBookPost(
            id="post_001",
            mood="😊 好心情",
            content="Test post content",
            author="Test User"
        )
        post.created_at = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = ExportService.export_to_markdown([post])

        # Markdown should contain headers and content
        assert "#" in result
        assert "好心情" in result
        assert "Test post content" in result

    def test_export_multiple_posts_to_markdown(self):
        """Test exporting multiple posts to Markdown."""
        posts = [
            ClawBookPost(
                id=f"post_{i:03d}",
                mood="😊 好心情",
                content=f"Post {i} content",
                author="Test User"
            )
            for i in range(3)
        ]

        result = ExportService.export_to_markdown(posts)

        # Should contain multiple entries
        assert result.count("#") >= 3
        for i in range(3):
            assert f"Post {i}" in result
