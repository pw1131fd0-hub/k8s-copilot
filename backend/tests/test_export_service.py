"""Tests for ExportService."""
import json
from datetime import datetime, timezone
import unittest
from backend.models.orm_models import ClawBookPost
from backend.services.export_service import ExportService


class TestExportService(unittest.TestCase):
    """Test cases for ExportService."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock posts
        self.posts = [
            ClawBookPost(
                id="post1",
                mood="😊 Happy",
                content="Today was a great day!",
                author="小龍蝦",
                like_count=5,
                comment_count=2,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
            ClawBookPost(
                id="post2",
                mood="💭 Thoughtful",
                content="I learned something new today.",
                author="小龍蝦",
                like_count=3,
                comment_count=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        ]

    def test_export_to_json(self):
        """Test JSON export format."""
        result = ExportService.export_to_json(self.posts)
        data = json.loads(result)

        self.assertIn("posts", data)
        self.assertIn("count", data)
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["posts"]), 2)
        self.assertEqual(data["posts"][0]["mood"], "😊 Happy")

    def test_export_to_json_with_metadata(self):
        """Test JSON export includes metadata."""
        result = ExportService.export_to_json(self.posts, include_metadata=True)
        data = json.loads(result)

        self.assertIn("exported_at", data)
        self.assertIn("format_version", data)
        self.assertEqual(data["format_version"], "1.0")

    def test_export_to_csv(self):
        """Test CSV export format."""
        result = ExportService.export_to_csv(self.posts)

        # Check that CSV has headers
        lines = result.strip().split("\n")
        self.assertGreater(len(lines), 1)
        self.assertIn("ID", lines[0])
        self.assertIn("Mood", lines[0])
        self.assertIn("Content", lines[0])

    def test_export_to_markdown(self):
        """Test Markdown export format."""
        result = ExportService.export_to_markdown(self.posts)

        # Check markdown structure
        self.assertIn("# ClawBook AI Journal Export", result)
        self.assertIn("😊 Happy", result)
        self.assertIn("💭 Thoughtful", result)
        self.assertIn("Total Posts", result)

    def test_get_file_extension(self):
        """Test file extension retrieval."""
        self.assertEqual(ExportService.get_file_extension("json"), ".json")
        self.assertEqual(ExportService.get_file_extension("csv"), ".csv")
        self.assertEqual(ExportService.get_file_extension("markdown"), ".md")

    def test_get_content_type(self):
        """Test content type retrieval."""
        self.assertEqual(ExportService.get_content_type("json"), "application/json")
        self.assertEqual(ExportService.get_content_type("csv"), "text/csv")
        self.assertEqual(ExportService.get_content_type("markdown"), "text/markdown")

    def test_export_empty_posts(self):
        """Test export with empty post list."""
        result = ExportService.export_to_json([])
        data = json.loads(result)

        self.assertEqual(data["count"], 0)
        self.assertEqual(len(data["posts"]), 0)

    def test_csv_truncates_long_content(self):
        """Test that CSV truncates long content."""
        long_post = ClawBookPost(
            id="post3",
            mood="🎯 Ambitious",
            content="x" * 150,  # 150 character content
            author="小龍蝦",
            like_count=0,
            comment_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = ExportService.export_to_csv([long_post])

        # Check that content is truncated with "..."
        self.assertIn("...", result)


if __name__ == "__main__":
    unittest.main()
