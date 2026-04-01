"""Collaboration API controller for ClawBook v1.6 - sharing, groups, and real-time features."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import asyncio

from backend.database import get_db
from backend.services.collaboration_service import CollaborationService
from backend.services.notification_service import NotificationService
from backend.models.schemas import (
    ShareCreateRequest,
    ShareResponse,
    GroupCreateRequest,
    GroupResponse,
    CommentCreateRequest,
    CommentResponse,
    ActivityLogResponse,
)

router = APIRouter(prefix="/collaboration", tags=["collaboration"])

# Default user ID for single-user mode (will be replaced with auth in future)
DEFAULT_USER_ID = "default_user"


def get_current_user_id() -> str:
    """Get current user ID. For single-user mode, always returns default user."""
    return DEFAULT_USER_ID


# ========== Share Endpoints ==========

@router.post("/posts/{post_id}/share", response_model=list[ShareResponse])
def share_post(
    post_id: str,
    request: ShareCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Share a post with users or groups."""
    try:
        shares = CollaborationService.share_post(
            db=db,
            post_id=post_id,
            owner_id=current_user_id,
            shared_with_ids=request.shared_with_ids,
            group_ids=request.group_ids,
            permission=request.permission or "read",
            expires_at=request.expires_at,
        )
        return [ShareResponse.from_orm(share) for share in shares]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts/shared-with-me", response_model=list[ShareResponse])
def get_shared_with_me(
    limit: int = Query(50, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get posts shared with the current user."""
    shares = CollaborationService.get_shared_with_me(db=db, user_id=current_user_id, limit=limit)
    return [ShareResponse.from_orm(share) for share in shares]


@router.post("/shares/{share_id}/accept", response_model=ShareResponse)
def accept_share(
    share_id: str,
    db: Session = Depends(get_db),
):
    """Accept a shared post."""
    try:
        share = CollaborationService.accept_share(db=db, share_id=share_id)
        return ShareResponse.from_orm(share)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/shares/{share_id}/reject", response_model=ShareResponse)
def reject_share(
    share_id: str,
    db: Session = Depends(get_db),
):
    """Reject a shared post."""
    try:
        share = CollaborationService.reject_share(db=db, share_id=share_id)
        return ShareResponse.from_orm(share)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/shares/{share_id}")
def delete_share(
    share_id: str,
    db: Session = Depends(get_db),
):
    """Revoke a shared post."""
    CollaborationService.revoke_share(db=db, share_id=share_id)
    return {"message": "Share revoked successfully"}


# ========== Group Endpoints ==========

@router.post("/groups", response_model=GroupResponse)
def create_group(
    request: GroupCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new collaboration group."""
    try:
        group = CollaborationService.create_group(
            db=db,
            name=request.name,
            creator_id=current_user_id,
            description=request.description,
            visibility=request.visibility or "private",
            icon=request.icon,
        )
        return GroupResponse.from_orm(group)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/groups/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: str,
    db: Session = Depends(get_db),
):
    """Get group details."""
    group = CollaborationService.get_group(db=db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return GroupResponse.from_orm(group)


@router.get("/groups", response_model=list[GroupResponse])
def list_user_groups(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all groups for the current user."""
    groups = CollaborationService.get_user_groups(db=db, user_id=current_user_id)
    return [GroupResponse.from_orm(group) for group in groups]


@router.post("/groups/{group_id}/members")
def add_group_members(
    group_id: str,
    user_ids: list[str],
    db: Session = Depends(get_db),
):
    """Add members to a group."""
    try:
        CollaborationService.add_group_members(db=db, group_id=group_id, user_ids=user_ids)
        return {"message": f"Added {len(user_ids)} members to group"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/groups/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: str,
    user_id: str,
    db: Session = Depends(get_db),
):
    """Remove a member from a group."""
    CollaborationService.remove_group_member(db=db, group_id=group_id, user_id=user_id)
    return {"message": "Member removed from group"}


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: str,
    db: Session = Depends(get_db),
):
    """Delete a group."""
    CollaborationService.delete_group(db=db, group_id=group_id)
    return {"message": "Group deleted successfully"}


# ========== Comment Endpoints ==========

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def add_comment(
    post_id: str,
    request: CommentCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a comment to a post and broadcast via WebSocket."""
    try:
        comment = CollaborationService.add_comment(
            db=db,
            post_id=post_id,
            user_id=current_user_id,
            content=request.content,
            is_suggestion=request.is_suggestion or False,
            parent_id=request.parent_id,
        )

        # Emit real-time comment notification
        await NotificationService.notify_comment_new(
            db=db,
            post_id=post_id,
            comment_id=comment.id,
            author_id=current_user_id,
            content=comment.content
        )

        return CommentResponse.from_orm(comment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def get_comments(
    post_id: str,
    include_replies: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get comments for a post."""
    comments = CollaborationService.get_comments(
        db=db, post_id=post_id, include_replies=include_replies
    )
    return [CommentResponse.from_orm(comment) for comment in comments]


@router.patch("/comments/{comment_id}")
async def update_comment_status(
    comment_id: str,
    status: str = Query(..., description="New status: open, accepted, rejected, resolved"),
    db: Session = Depends(get_db),
):
    """Update comment status (accept/reject suggestion) and broadcast via WebSocket."""
    try:
        comment = CollaborationService.update_comment_status(db=db, comment_id=comment_id, status=status)

        # Emit update notification
        await NotificationService.notify_comment_updated(
            db=db,
            post_id=comment.post_id,
            comment_id=comment.id,
            content=comment.content
        )

        return CommentResponse.from_orm(comment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
):
    """Delete a comment and broadcast via WebSocket."""
    try:
        # Get comment before deletion to find its post_id
        from backend.models.orm_models import CollaborationComment
        comment = db.query(CollaborationComment).filter(CollaborationComment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        post_id = comment.post_id

        # Delete the comment
        CollaborationService.delete_comment(db=db, comment_id=comment_id)

        # Emit deletion notification
        await NotificationService.notify_comment_deleted(
            db=db,
            post_id=post_id,
            comment_id=comment_id
        )

        return {"message": "Comment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Activity Log Endpoints ==========

@router.get("/groups/{group_id}/activity", response_model=list[ActivityLogResponse])
def get_group_activity(
    group_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get activity logs for a group."""
    logs = CollaborationService.get_group_activity(db=db, group_id=group_id, limit=limit)
    return [ActivityLogResponse.from_orm(log) for log in logs]
