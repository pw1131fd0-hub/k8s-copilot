"""Export service for ClawBook posts in multiple formats."""
import json
import csv
from io import StringIO
from datetime import datetime, timezone
from typing import List
from backend.models.orm_models import ClawBookPost


class ExportService:
    """Service for exporting ClawBook posts in various formats."""

    @staticmethod
    def export_to_json(posts: List[ClawBookPost], include_metadata: bool = True) -> str:
        """
        Export posts to JSON format.

        Args:
            posts: List of ClawBookPost objects to export
            include_metadata: Whether to include export metadata

        Returns:
            JSON string representation of posts
        """
        posts_data = [
            {
                "id": post.id,
                "mood": post.mood,
                "content": post.content,
                "author": post.author,
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "updated_at": post.updated_at.isoformat() if post.updated_at else None,
            }
            for post in posts
        ]

        result = {
            "posts": posts_data,
            "count": len(posts),
        }

        if include_metadata:
            result["exported_at"] = datetime.now(timezone.utc).isoformat()
            result["format_version"] = "1.0"

        return json.dumps(result, ensure_ascii=False, indent=2)

    @staticmethod
    def export_to_csv(posts: List[ClawBookPost]) -> str:
        """
        Export posts to CSV format.

        Args:
            posts: List of ClawBookPost objects to export

        Returns:
            CSV string representation of posts
        """
        output = StringIO()
        fieldnames = ["ID", "Mood", "Content", "Author", "Likes", "Comments", "Created At", "Updated At"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for post in posts:
            writer.writerow({
                "ID": post.id,
                "Mood": post.mood,
                "Content": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                "Author": post.author,
                "Likes": post.like_count,
                "Comments": post.comment_count,
                "Created At": post.created_at.isoformat() if post.created_at else "",
                "Updated At": post.updated_at.isoformat() if post.updated_at else "",
            })

        return output.getvalue()

    @staticmethod
    def export_to_markdown(posts: List[ClawBookPost]) -> str:
        """
        Export posts to Markdown format.

        Args:
            posts: List of ClawBookPost objects to export

        Returns:
            Markdown string representation of posts
        """
        lines = [
            "# ClawBook AI Journal Export",
            f"**Export Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Total Posts**: {len(posts)}",
            "",
        ]

        for i, post in enumerate(posts, 1):
            created_date = post.created_at.strftime("%Y-%m-%d %H:%M") if post.created_at else "Unknown"
            lines.append(f"## Post {i}: {post.mood}")
            lines.append(f"**Author**: {post.author} | **Date**: {created_date}")
            lines.append(f"**Engagement**: {post.like_count} likes, {post.comment_count} comments")
            lines.append("")
            lines.append(post.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def get_file_extension(format_type: str) -> str:
        """Get file extension for given export format."""
        extensions = {
            "json": ".json",
            "csv": ".csv",
            "markdown": ".md",
        }
        return extensions.get(format_type, ".txt")

    @staticmethod
    def get_content_type(format_type: str) -> str:
        """Get MIME type for given export format."""
        content_types = {
            "json": "application/json",
            "csv": "text/csv",
            "markdown": "text/markdown",
        }
        return content_types.get(format_type, "text/plain")
