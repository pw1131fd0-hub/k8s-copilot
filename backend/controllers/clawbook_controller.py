"""ClawBook API controller for diary posts, likes, comments, and images."""
import uuid
from datetime import datetime, timezone, date
from typing import Annotated
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.orm_models import (
    ClawBookPost,
    ClawBookComment,
    ClawBookLike,
    ClawBookImage,
    AIDecisionPath,
)
from backend.models.schemas import (
    ClawBookPostCreate,
    ClawBookPostResponse,
    ClawBookPostListResponse,
    ClawBookCommentCreate,
    ClawBookCommentResponse,
    ClawBookImageCreate,
    ClawBookMoodSummaryResponse,
    ClawBookMoodStats,
    AIDecisionPathCreate,
    AIDecisionPathResponse,
    AIDecisionPathHistoryResponse,
    AIDecisionPathSummary,
)
from backend.services.export_service import ExportService

router = APIRouter(prefix="/clawbook", tags=["clawbook"])

# Default user ID for single-user mode
DEFAULT_USER_ID = "default_user"


def get_current_user_id() -> str:
    """Get current user ID. For single-user mode, always returns default user."""
    return DEFAULT_USER_ID


def _post_to_response(post: ClawBookPost, user_id: str, db: Session) -> ClawBookPostResponse:
    """Convert a ClawBookPost ORM model to response schema."""
    # Check if current user liked this post
    liked = (
        db.query(ClawBookLike)
        .filter(
            ClawBookLike.post_id == post.id,
            ClawBookLike.user_id == user_id,
        )
        .first()
        is not None
    )

    # Get comments
    comments = (
        db.query(ClawBookComment)
        .filter(ClawBookComment.post_id == post.id)
        .order_by(ClawBookComment.created_at.desc())
        .all()
    )

    # Get images
    images = (
        db.query(ClawBookImage)
        .filter(ClawBookImage.post_id == post.id)
        .all()
    )

    return ClawBookPostResponse(
        id=post.id,
        mood=post.mood,
        content=post.content,
        author=post.author,
        like_count=post.like_count,
        comment_count=post.comment_count,
        liked=liked,
        comments=[
            ClawBookCommentResponse(
                id=c.id,
                author=c.author,
                text=c.text,
                created_at=c.created_at,
            )
            for c in comments
        ],
        images=[img.image_data for img in images],
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


# ============================================================================
# Posts API
# ============================================================================


@router.post("/posts", response_model=ClawBookPostResponse)
def create_post(
    post_data: ClawBookPostCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ClawBookPostResponse:
    """Create a new ClawBook post with optional images."""
    # Create post
    post = ClawBookPost(
        id=str(uuid.uuid4()),
        mood=post_data.mood,
        content=post_data.content,
        author=post_data.author,
        like_count=0,
        comment_count=0,
    )
    db.add(post)

    # Add images if provided
    for idx, image_data in enumerate(post_data.images):
        image = ClawBookImage(
            id=str(uuid.uuid4()),
            post_id=post.id,
            image_data=image_data,
            filename=f"image_{idx}.jpg",
            content_type="image/jpeg",
        )
        db.add(image)

    db.commit()
    db.refresh(post)

    return _post_to_response(post, user_id, db)


@router.get("/posts", response_model=ClawBookPostListResponse)
def list_posts(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ClawBookPostListResponse:
    """List all ClawBook posts with pagination."""
    # Get total count
    total = db.query(ClawBookPost).count()

    # Get posts
    posts = (
        db.query(ClawBookPost)
        .order_by(ClawBookPost.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ClawBookPostListResponse(
        posts=[_post_to_response(post, user_id, db) for post in posts],
        total=total,
    )


@router.get("/posts/{post_id}", response_model=ClawBookPostResponse)
def get_post(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ClawBookPostResponse:
    """Get a specific ClawBook post by ID."""
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_response(post, user_id, db)


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict:
    """Delete a ClawBook post."""
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}


# ============================================================================
# Likes API
# ============================================================================


@router.post("/posts/{post_id}/like", response_model=dict)
def toggle_like(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict:
    """Toggle like status for a post."""
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if already liked
    existing_like = (
        db.query(ClawBookLike)
        .filter(
            ClawBookLike.post_id == post_id,
            ClawBookLike.user_id == user_id,
        )
        .first()
    )

    if existing_like:
        # Unlike
        db.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        liked = False
    else:
        # Like
        new_like = ClawBookLike(
            id=str(uuid.uuid4()),
            post_id=post_id,
            user_id=user_id,
        )
        db.add(new_like)
        post.like_count += 1
        liked = True

    db.commit()

    return {"liked": liked, "like_count": post.like_count}


# ============================================================================
# Comments API
# ============================================================================


@router.post("/posts/{post_id}/comments", response_model=ClawBookCommentResponse)
def add_comment(
    post_id: str,
    comment_data: ClawBookCommentCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ClawBookCommentResponse:
    """Add a comment to a post."""
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = ClawBookComment(
        id=str(uuid.uuid4()),
        post_id=post_id,
        author=comment_data.author,
        text=comment_data.text,
    )
    db.add(comment)

    # Update comment count
    post.comment_count += 1

    db.commit()
    db.refresh(comment)

    return ClawBookCommentResponse(
        id=comment.id,
        author=comment.author,
        text=comment.text,
        created_at=comment.created_at,
    )


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict:
    """Delete a comment."""
    comment = db.query(ClawBookComment).filter(ClawBookComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Update comment count
    post = db.query(ClawBookPost).filter(ClawBookPost.id == comment.post_id).first()
    if post:
        post.comment_count = max(0, post.comment_count - 1)

    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted successfully"}


# ============================================================================
# Images API
# ============================================================================


@router.post("/posts/{post_id}/images", response_model=dict)
def add_images(
    post_id: str,
    images: list[ClawBookImageCreate],
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict:
    """Add images to an existing post."""
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    for idx, image_data in enumerate(images):
        image = ClawBookImage(
            id=str(uuid.uuid4()),
            post_id=post_id,
            image_data=image_data.image_data,
            filename=image_data.filename or f"image_{idx}.jpg",
            content_type=image_data.content_type or "image/jpeg",
        )
        db.add(image)

    db.commit()

    return {"message": f"Added {len(images)} image(s) successfully"}


# ============================================================================
# Mood Statistics API
# ============================================================================


@router.get("/mood-summary", response_model=ClawBookMoodSummaryResponse)
def get_mood_summary(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    days: Annotated[int, Query(ge=1, le=365)] = 7,
) -> ClawBookMoodSummaryResponse:
    """Get mood summary statistics for the specified number of days."""
    from datetime import timedelta

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get posts within the time period
    posts = (
        db.query(ClawBookPost)
        .filter(ClawBookPost.created_at >= cutoff_date)
        .all()
    )

    # Count moods
    mood_counts: dict[str, int] = {}
    for post in posts:
        mood_counts[post.mood] = mood_counts.get(post.mood, 0) + 1

    # Convert to response format
    mood_stats = [
        ClawBookMoodStats(mood=mood, count=count)
        for mood, count in sorted(mood_counts.items(), key=lambda x: -x[1])
    ]

    return ClawBookMoodSummaryResponse(
        mood_stats=mood_stats,
        total_posts=len(posts),
    )


# ============================================================================
# Export API
# ============================================================================


@router.get("/posts/export")
def export_posts(
    format: Annotated[str, Query(pattern="^(json|csv|markdown)$")] = "json",
    start_date: Annotated[str, Query()] = None,
    end_date: Annotated[str, Query()] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    user_id: Annotated[str, Depends(get_current_user_id)] = None,
):
    """
    Export posts in specified format.

    Args:
        format: Export format (json, csv, markdown)
        start_date: Filter by start date (YYYY-MM-DD format)
        end_date: Filter by end date (YYYY-MM-DD format)

    Returns:
        File download response
    """
    # Query posts with optional date filtering
    query = db.query(ClawBookPost)

    if start_date:
        try:
            start = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
            query = query.filter(ClawBookPost.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            end = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
            query = query.filter(ClawBookPost.created_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    posts = query.order_by(ClawBookPost.created_at.desc()).all()

    # Export based on format
    if format == "json":
        content = ExportService.export_to_json(posts)
        media_type = "application/json"
        filename = f"clawbook_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    elif format == "csv":
        content = ExportService.export_to_csv(posts)
        media_type = "text/csv; charset=utf-8"
        filename = f"clawbook_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    elif format == "markdown":
        content = ExportService.export_to_markdown(posts)
        media_type = "text/markdown; charset=utf-8"
        filename = f"clawbook_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    # Return as downloadable file
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============================================================================
# AI Decision Path Visualization API (v1.4)
# ============================================================================


@router.get("/posts/{post_id}/decision-path", response_model=AIDecisionPathResponse)
def get_decision_path(
    post_id: str,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> AIDecisionPathResponse:
    """Get AI decision path for a specific post."""
    # Verify post exists
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Get decision path
    decision_path = db.query(AIDecisionPath).filter(AIDecisionPath.post_id == post_id).first()
    if not decision_path:
        raise HTTPException(
            status_code=404,
            detail=f"No decision path found for post {post_id}. Run analysis to generate it.",
        )

    return AIDecisionPathResponse(
        post_id=decision_path.post_id,
        reasoning_steps=decision_path.reasoning_steps,
        candidates=decision_path.candidates,
        final_decision=decision_path.final_decision,
        key_factors=decision_path.key_factors,
        model_used=decision_path.model_used,
        decision_time_ms=decision_path.decision_time_ms,
        created_at=decision_path.created_at,
        updated_at=decision_path.updated_at,
    )


@router.post("/posts/{post_id}/decision-path", response_model=dict)
def create_or_update_decision_path(
    post_id: str,
    path_data: AIDecisionPathCreate,
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict:
    """Create or update AI decision path for a post."""
    # Verify post exists
    post = db.query(ClawBookPost).filter(ClawBookPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")

    # Check if decision path already exists
    existing = db.query(AIDecisionPath).filter(AIDecisionPath.post_id == post_id).first()

    # Convert Pydantic models to dictionaries for JSON storage
    reasoning_steps_list = [step.model_dump() for step in path_data.reasoning_steps]
    candidates_list = [cand.model_dump() for cand in path_data.candidates]
    final_decision_dict = path_data.final_decision.model_dump()
    key_factors_list = [factor.model_dump() for factor in path_data.key_factors]

    if existing:
        # Update existing
        existing.reasoning_steps = reasoning_steps_list
        existing.candidates = candidates_list
        existing.final_decision = final_decision_dict
        existing.key_factors = key_factors_list
        existing.model_used = path_data.model_used
        existing.decision_time_ms = path_data.decision_time_ms
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {
            "message": "Decision path updated successfully",
            "post_id": post_id,
            "status": "updated",
        }
    else:
        # Create new
        new_path = AIDecisionPath(
            id=str(uuid.uuid4()),
            post_id=post_id,
            reasoning_steps=reasoning_steps_list,
            candidates=candidates_list,
            final_decision=final_decision_dict,
            key_factors=key_factors_list,
            model_used=path_data.model_used,
            decision_time_ms=path_data.decision_time_ms,
        )
        db.add(new_path)
        db.commit()
        return {
            "message": "Decision path created successfully",
            "post_id": post_id,
            "status": "created",
        }


@router.get("/decision-paths/history", response_model=AIDecisionPathHistoryResponse)
def get_decision_paths_history(
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    start_date: Annotated[str, Query()] = None,
    end_date: Annotated[str, Query()] = None,
    model: Annotated[str, Query()] = None,
) -> AIDecisionPathHistoryResponse:
    """Get history of AI decision paths with optional filtering."""
    query = db.query(AIDecisionPath)

    # Apply filters
    if start_date:
        try:
            start = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
            query = query.filter(AIDecisionPath.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

    if end_date:
        try:
            end = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
            query = query.filter(AIDecisionPath.created_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

    if model:
        query = query.filter(AIDecisionPath.model_used == model)

    # Get total count
    total = query.count()

    # Get paginated results
    paths = (
        query.order_by(AIDecisionPath.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Convert to summary format
    summaries = [
        AIDecisionPathSummary(
            post_id=path.post_id,
            model_used=path.model_used,
            final_decision_option=path.final_decision.get("option", ""),
            confidence_score=path.final_decision.get("confidence_score", 0.0),
            decision_time_ms=path.decision_time_ms,
            created_at=path.created_at,
        )
        for path in paths
    ]

    return AIDecisionPathHistoryResponse(total=total, paths=summaries)
