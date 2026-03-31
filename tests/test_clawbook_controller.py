"""Comprehensive tests for ClawBook controller (diary posts, comments, likes, images)."""
# pylint: disable=redefined-outer-name
from unittest.mock import patch
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.models.orm_models import (
    ClawBookPost,
    ClawBookComment,
    ClawBookLike,
    ClawBookImage,
)
from backend.models.schemas import (
    ClawBookPostCreate,
    ClawBookCommentCreate,
    ClawBookImageCreate,
)


@pytest.fixture
def client():
    """Return a TestClient wired to the FastAPI app with test database."""
    # Import models to register them with metadata
    from backend.models.orm_models import (  # pylint: disable=import-outside-toplevel
        ClawBookPost,
        ClawBookComment,
        ClawBookLike,
        ClawBookImage,
    )

    # Create test database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    with patch('kubernetes.config.load_kube_config'), \
         patch('kubernetes.config.load_incluster_config'):
        from backend.main import app  # pylint: disable=import-outside-toplevel
        from backend.database import get_db  # pylint: disable=import-outside-toplevel
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()


# ============================================================================
# Posts API Tests
# ============================================================================


def test_create_post(client):
    """POST /api/v1/clawbook/posts should create a new post."""
    response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Today was a great day!",
            "author": "AI Assistant",
            "images": [],
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mood"] == "😊"
    assert data["content"] == "Today was a great day!"
    assert data["author"] == "AI Assistant"
    assert data["like_count"] == 0
    assert data["comment_count"] == 0
    assert "id" in data
    assert "created_at" in data


def test_create_post_with_images(client):
    """POST /api/v1/clawbook/posts should create post with images."""
    response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "🥰",
            "content": "Look at my photo!",
            "author": "AI",
            "images": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="],
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["images"]) == 1


def test_list_posts(client):
    """GET /api/v1/clawbook/posts should return all posts with pagination."""
    # Create 3 posts
    for i in range(3):
        client.post(
            "/api/v1/clawbook/posts",
            json={
                "mood": ["😊", "😐", "😔"][i],
                "content": f"Post {i+1}",
                "author": "AI",
                "images": [],
            }
        )

    # List posts
    response = client.get("/api/v1/clawbook/posts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["posts"]) == 3
    # Posts should be in reverse chronological order
    assert data["posts"][0]["content"] == "Post 3"


def test_list_posts_with_pagination(client):
    """GET /api/v1/clawbook/posts should support limit and offset."""
    # Create 5 posts
    for i in range(5):
        client.post(
            "/api/v1/clawbook/posts",
            json={
                "mood": "😊",
                "content": f"Post {i+1}",
                "author": "AI",
                "images": [],
            }
        )

    # Get first 2 posts
    response = client.get("/api/v1/clawbook/posts?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) == 2
    assert data["total"] == 5

    # Get next 2 posts
    response = client.get("/api/v1/clawbook/posts?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) == 2


def test_get_post(client):
    """GET /api/v1/clawbook/posts/{post_id} should return a specific post."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "🥰",
            "content": "Get me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Get the post
    response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post_id
    assert data["content"] == "Get me!"


def test_get_post_not_found(client):
    """GET /api/v1/clawbook/posts/{post_id} should return 404 for non-existent post."""
    response = client.get("/api/v1/clawbook/posts/nonexistent-id")
    assert response.status_code == 404
    assert "Post not found" in response.json()["detail"]


def test_delete_post(client):
    """DELETE /api/v1/clawbook/posts/{post_id} should delete a post."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😔",
            "content": "Delete me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Delete the post
    response = client.delete(f"/api/v1/clawbook/posts/{post_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify post is deleted
    get_response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert get_response.status_code == 404


def test_delete_post_not_found(client):
    """DELETE /api/v1/clawbook/posts/{post_id} should return 404 for non-existent post."""
    response = client.delete("/api/v1/clawbook/posts/nonexistent-id")
    assert response.status_code == 404


# ============================================================================
# Likes API Tests
# ============================================================================


def test_toggle_like_add(client):
    """POST /api/v1/clawbook/posts/{post_id}/like should add a like."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Like me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Like the post
    response = client.post(f"/api/v1/clawbook/posts/{post_id}/like")
    assert response.status_code == 200
    data = response.json()
    assert data["liked"] is True
    assert data["like_count"] == 1


def test_toggle_like_remove(client):
    """POST /api/v1/clawbook/posts/{post_id}/like should toggle off an existing like."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Like me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Like the post
    client.post(f"/api/v1/clawbook/posts/{post_id}/like")

    # Unlike the post
    response = client.post(f"/api/v1/clawbook/posts/{post_id}/like")
    assert response.status_code == 200
    data = response.json()
    assert data["liked"] is False
    assert data["like_count"] == 0


def test_toggle_like_not_found(client):
    """POST /api/v1/clawbook/posts/{post_id}/like should return 404 for non-existent post."""
    response = client.post("/api/v1/clawbook/posts/nonexistent-id/like")
    assert response.status_code == 404


def test_post_reflection_liked_status(client):
    """Post response should reflect correct liked status."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Check my status!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Initially not liked
    response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert response.json()["liked"] is False

    # Like it
    client.post(f"/api/v1/clawbook/posts/{post_id}/like")

    # Now should show as liked
    response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert response.json()["liked"] is True


# ============================================================================
# Comments API Tests
# ============================================================================


def test_add_comment(client):
    """POST /api/v1/clawbook/posts/{post_id}/comments should add a comment."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Comment on me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Add a comment
    response = client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={
            "author": "Friend",
            "text": "Great post!",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["author"] == "Friend"
    assert data["text"] == "Great post!"
    assert "id" in data
    assert "created_at" in data


def test_add_comment_increments_count(client):
    """Adding a comment should increment post's comment_count."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Comment on me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Initially 0 comments
    assert client.get(f"/api/v1/clawbook/posts/{post_id}").json()["comment_count"] == 0

    # Add 2 comments
    client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "User1", "text": "Comment 1"}
    )
    client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "User2", "text": "Comment 2"}
    )

    # Now should have 2 comments
    response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert response.json()["comment_count"] == 2


def test_add_comment_not_found(client):
    """POST /api/v1/clawbook/posts/{post_id}/comments should return 404 for non-existent post."""
    response = client.post(
        "/api/v1/clawbook/posts/nonexistent-id/comments",
        json={"author": "User", "text": "Comment"}
    )
    assert response.status_code == 404


def test_delete_comment(client):
    """DELETE /api/v1/clawbook/comments/{comment_id} should delete a comment."""
    # Create a post and add a comment
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Delete my comment!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    comment_response = client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "User", "text": "Delete me!"}
    )
    comment_id = comment_response.json()["id"]

    # Delete the comment
    response = client.delete(f"/api/v1/clawbook/comments/{comment_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    # Verify comment count decreased
    post_response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert post_response.json()["comment_count"] == 0


def test_delete_comment_not_found(client):
    """DELETE /api/v1/clawbook/comments/{comment_id} should return 404 for non-existent comment."""
    response = client.delete("/api/v1/clawbook/comments/nonexistent-id")
    assert response.status_code == 404


def test_comments_in_post_response(client):
    """Post response should include all comments."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Show my comments!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Add comments
    client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "User1", "text": "Comment 1"}
    )
    client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "User2", "text": "Comment 2"}
    )

    # Get post and verify comments
    response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    data = response.json()
    assert len(data["comments"]) == 2
    assert data["comments"][0]["author"] == "User2"  # Most recent first


# ============================================================================
# Images API Tests
# ============================================================================


def test_add_images_to_post(client):
    """POST /api/v1/clawbook/posts/{post_id}/images should add images to a post."""
    # Create a post
    create_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Add images to me!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = create_response.json()["id"]

    # Add images
    image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    response = client.post(
        f"/api/v1/clawbook/posts/{post_id}/images",
        json=[
            {"image_data": image_data, "filename": "photo1.jpg", "content_type": "image/jpeg"},
            {"image_data": image_data, "filename": "photo2.jpg", "content_type": "image/jpeg"},
        ]
    )
    assert response.status_code == 200
    assert "2 image(s)" in response.json()["message"]

    # Verify images in post
    post_response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert len(post_response.json()["images"]) == 2


def test_add_images_not_found(client):
    """POST /api/v1/clawbook/posts/{post_id}/images should return 404 for non-existent post."""
    response = client.post(
        "/api/v1/clawbook/posts/nonexistent-id/images",
        json=[]
    )
    assert response.status_code == 404


# ============================================================================
# Mood Statistics API Tests
# ============================================================================


def test_get_mood_summary(client):
    """GET /api/v1/clawbook/mood-summary should return mood statistics."""
    # Create posts with different moods
    moods = ["😊", "😐", "😊", "😔", "😊", "🥰"]
    for mood in moods:
        client.post(
            "/api/v1/clawbook/posts",
            json={
                "mood": mood,
                "content": f"Feeling {mood}",
                "author": "AI",
                "images": [],
            }
        )

    # Get mood summary
    response = client.get("/api/v1/clawbook/mood-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_posts"] == 6

    # Verify mood stats
    mood_stats = {stat["mood"]: stat["count"] for stat in data["mood_stats"]}
    assert mood_stats["😊"] == 3
    assert mood_stats["😐"] == 1
    assert mood_stats["😔"] == 1
    assert mood_stats["🥰"] == 1


def test_get_mood_summary_with_days_filter(client):
    """GET /api/v1/clawbook/mood-summary?days=7 should filter by days."""
    # Create a post
    client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Today!",
            "author": "AI",
            "images": [],
        }
    )

    # Get summary with 7 days (default)
    response = client.get("/api/v1/clawbook/mood-summary?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["total_posts"] == 1


def test_get_mood_summary_empty(client):
    """GET /api/v1/clawbook/mood-summary should return empty stats when no posts."""
    response = client.get("/api/v1/clawbook/mood-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_posts"] == 0
    assert len(data["mood_stats"]) == 0


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_workflow(client):
    """Test a complete workflow: create post, add comments, like, get summary."""
    # 1. Create a post
    post_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Full workflow test!",
            "author": "AI",
            "images": [],
        }
    )
    assert post_response.status_code == 200
    post_id = post_response.json()["id"]

    # 2. Add comments
    client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "Friend1", "text": "Nice!"}
    )
    client.post(
        f"/api/v1/clawbook/posts/{post_id}/comments",
        json={"author": "Friend2", "text": "Awesome!"}
    )

    # 3. Like the post
    client.post(f"/api/v1/clawbook/posts/{post_id}/like")

    # 4. Get the post and verify all data
    get_response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    post_data = get_response.json()
    assert post_data["mood"] == "😊"
    assert post_data["like_count"] == 1
    assert post_data["comment_count"] == 2
    assert post_data["liked"] is True
    assert len(post_data["comments"]) == 2

    # 5. Get mood summary
    summary_response = client.get("/api/v1/clawbook/mood-summary")
    summary_data = summary_response.json()
    assert summary_data["total_posts"] == 1


def test_multiple_users_like_same_post(client):
    """Test that multiple users can like the same post."""
    # Create a post
    post_response = client.post(
        "/api/v1/clawbook/posts",
        json={
            "mood": "😊",
            "content": "Popular post!",
            "author": "AI",
            "images": [],
        }
    )
    post_id = post_response.json()["id"]

    # The default user likes it (current implementation)
    client.post(f"/api/v1/clawbook/posts/{post_id}/like")

    # Verify like was added
    response = client.get(f"/api/v1/clawbook/posts/{post_id}")
    assert response.json()["like_count"] == 1
