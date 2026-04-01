"""Pydantic request/response schemas for the Lobster K8s Copilot API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

from backend.utils import K8S_NAME_RE

_YAML_MAX_BYTES = 512 * 1024  # 512 KB

# ============================================================================
# ClawBook AI 日誌系統 Schemas
# ============================================================================


class ClawBookImageBase(BaseModel):
    """Base schema for ClawBook images."""
    filename: str | None = None
    content_type: str | None = None


class ClawBookImageCreate(ClawBookImageBase):
    """Schema for creating a ClawBook image."""
    image_data: str  # Base64 encoded


class ClawBookImageResponse(ClawBookImageBase):
    """Schema for ClawBook image response."""
    id: str
    image_data: str

    model_config = {"from_attributes": True}


class ClawBookCommentBase(BaseModel):
    """Base schema for ClawBook comments."""
    text: str


class ClawBookCommentCreate(ClawBookCommentBase):
    """Schema for creating a ClawBook comment."""
    author: str = "我"


class ClawBookCommentResponse(ClawBookCommentBase):
    """Schema for ClawBook comment response."""
    id: str
    author: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClawBookLikeResponse(BaseModel):
    """Schema for ClawBook like response."""
    id: str
    post_id: str
    user_id: str
    liked: bool = True

    model_config = {"from_attributes": True}


class ClawBookPostBase(BaseModel):
    """Base schema for ClawBook posts."""
    mood: str
    content: str


class ClawBookPostCreate(ClawBookPostBase):
    """Schema for creating a ClawBook post."""
    author: str = "小龍蝦"
    images: list[str] = []  # Base64 encoded images


class ClawBookPostResponse(ClawBookPostBase):
    """Schema for ClawBook post response."""
    id: str
    author: str
    like_count: int
    comment_count: int
    liked: bool = False  # Current user's like status
    comments: list[ClawBookCommentResponse] = []
    images: list[str] = []  # Base64 encoded images
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ClawBookPostListResponse(BaseModel):
    """Schema for listing ClawBook posts."""
    posts: list[ClawBookPostResponse]
    total: int


class ClawBookMoodStats(BaseModel):
    """Schema for mood statistics."""
    mood: str
    count: int


class ClawBookMoodSummaryResponse(BaseModel):
    """Schema for mood summary response."""
    mood_stats: list[ClawBookMoodStats]
    total_posts: int


class PodInfo(BaseModel):
    """Represents a single Kubernetes pod with basic status fields."""

    name: str
    namespace: str
    status: str | None
    ip: str | None
    conditions: list[dict] = []


class PodListResponse(BaseModel):
    """Response model for pod listing endpoints."""

    pods: list[PodInfo]
    total: int


class DiagnoseRequest(BaseModel):
    """Request body for triggering AI diagnosis on a pod."""

    namespace: str = "default"
    force: bool = False

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Ensure namespace follows Kubernetes DNS-subdomain naming rules."""
        if not K8S_NAME_RE.match(v):
            raise ValueError(
                "namespace must be a valid Kubernetes name (lowercase alphanumeric and hyphens)"
            )
        return v


class DiagnoseResponse(BaseModel):
    """Response model containing AI-generated diagnosis for a Kubernetes pod."""

    pod_name: str
    namespace: str
    error_type: str | None
    root_cause: str
    detailed_analysis: str | None = None
    remediation: str
    raw_analysis: str
    model_used: str


class YamlScanRequest(BaseModel):
    """Request body for YAML manifest scanning."""

    yaml_content: str
    filename: str | None = "manifest.yaml"

    @field_validator("yaml_content")
    @classmethod
    def validate_yaml_size(cls, v: str) -> str:
        """Reject YAML payloads exceeding the maximum allowed byte size."""
        if len(v.encode("utf-8")) > _YAML_MAX_BYTES:
            raise ValueError(
                f"yaml_content exceeds maximum allowed size of {_YAML_MAX_BYTES // 1024} KB"
            )
        return v


class YamlIssue(BaseModel):
    """A single issue detected during YAML manifest scanning."""

    severity: Literal["ERROR", "WARNING", "INFO"]
    rule: str
    message: str
    line: int | None = None


class YamlScanResponse(BaseModel):
    """Response model for YAML scan results, including all detected issues."""

    filename: str
    issues: list[YamlIssue]
    total_issues: int
    has_errors: bool
    ai_suggestions: str | None = None


class DiagnoseHistoryRecord(BaseModel):
    """A persisted diagnosis record retrieved from the database."""

    id: str
    pod_name: str
    namespace: str
    error_type: str | None
    ai_analysis: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Slack Integration Schemas
# ============================================================================


class SlackConfigBase(BaseModel):
    """Base schema for Slack configuration."""
    webhook_url: str
    enabled: bool = True
    summary_enabled: bool = True
    summary_time: str = "09:00"
    high_mood_enabled: bool = True
    high_mood_threshold: int = 4
    milestone_enabled: bool = True
    include_full_content: bool = False


class SlackConfigCreate(SlackConfigBase):
    """Schema for creating Slack configuration."""
    pass


class SlackConfigUpdate(BaseModel):
    """Schema for updating Slack configuration."""
    webhook_url: str | None = None
    enabled: bool | None = None
    summary_enabled: bool | None = None
    summary_time: str | None = None
    high_mood_enabled: bool | None = None
    high_mood_threshold: int | None = None
    milestone_enabled: bool | None = None
    include_full_content: bool | None = None


class SlackConfigResponse(SlackConfigBase):
    """Schema for Slack configuration response."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# AI Decision Path Visualization Schemas (v1.4)
# ============================================================================


class ReasoningStep(BaseModel):
    """A single reasoning step in the AI decision process."""
    step_number: int
    title: str
    description: str
    intermediate_conclusion: str
    timestamp_ms: int


class DecisionCandidate(BaseModel):
    """A candidate option considered by the AI during decision making."""
    option: str
    score: float  # 0.0 - 1.0
    reasoning: str
    rejected_at_step: int | None = None


class FinalDecision(BaseModel):
    """The final decision made by the AI."""
    option: str
    confidence_score: float  # 0.0 - 1.0
    rationale: str


class KeyFactor(BaseModel):
    """A key factor influencing the AI decision."""
    factor: str
    weight: float  # 0.0 - 1.0
    influence: Literal["positive", "negative", "neutral"]
    description: str


class AIDecisionPathBase(BaseModel):
    """Base schema for AI decision path."""
    reasoning_steps: list[ReasoningStep]
    candidates: list[DecisionCandidate]
    final_decision: FinalDecision
    key_factors: list[KeyFactor]
    model_used: str | None = None
    decision_time_ms: int | None = None


class AIDecisionPathCreate(AIDecisionPathBase):
    """Schema for creating an AI decision path."""
    pass


class AIDecisionPathResponse(AIDecisionPathBase):
    """Schema for AI decision path response."""
    post_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIDecisionPathSummary(BaseModel):
    """Summary schema for listing decision paths."""
    post_id: str
    model_used: str | None
    final_decision_option: str
    confidence_score: float
    decision_time_ms: int | None
    created_at: datetime


class AIDecisionPathHistoryResponse(BaseModel):
    """Schema for decision path history listing."""
    total: int
    paths: list[AIDecisionPathSummary]


# ============================================================================
# Collaboration Schemas (v1.6)
# ============================================================================


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    username: str
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class ShareCreateRequest(BaseModel):
    """Request schema for creating a share."""
    shared_with_ids: list[str] | None = None
    group_ids: list[str] | None = None
    permission: str = "read"  # "read", "comment", "edit"
    expires_at: datetime | None = None


class ShareResponse(BaseModel):
    """Response schema for share."""
    id: str
    post_id: str
    owner_id: str
    shared_with_id: str | None = None
    group_id: str | None = None
    permission: str
    status: str  # "pending", "accepted", "rejected"
    created_at: datetime
    accepted_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class GroupCreateRequest(BaseModel):
    """Request schema for creating a group."""
    name: str
    description: str | None = None
    visibility: str = "private"  # "private", "team", "public"
    icon: str | None = None


class GroupResponse(BaseModel):
    """Response schema for group."""
    id: str
    name: str
    description: str | None = None
    creator_id: str
    visibility: str
    icon: str | None = None
    created_at: datetime
    updated_at: datetime
    members: list[UserResponse] = []

    model_config = {"from_attributes": True}


class CommentCreateRequest(BaseModel):
    """Request schema for creating a comment."""
    content: str
    is_suggestion: bool = False
    parent_id: str | None = None


class CommentResponse(BaseModel):
    """Response schema for comment."""
    id: str
    post_id: str
    user_id: str
    content: str
    is_suggestion: bool = False
    status: str  # "open", "accepted", "rejected", "resolved"
    parent_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogResponse(BaseModel):
    """Response schema for activity log."""
    id: str
    group_id: str | None = None
    actor_id: str
    action: str
    target_type: str
    target_id: str
    activity_data: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Sentiment Analytics Schemas (v1.7)
# ============================================================================


class SentimentTrendPoint(BaseModel):
    """Single data point in a sentiment trend."""
    date: str | None = None
    week: str | None = None
    month: str | None = None
    sentiment: float
    post_count: int


class HeatmapPoint(BaseModel):
    """Single data point in sentiment heatmap."""
    week: int
    day: str
    sentiment: float
    post_count: int


class SentimentTrendResponse(BaseModel):
    """Response schema for sentiment trends."""
    period_days: int
    granularity: str
    total_posts: int
    average_sentiment: float
    min_sentiment: float
    max_sentiment: float
    trends: list[SentimentTrendPoint]
    insights: list[str]


class SentimentAnalyticsResponse(SentimentTrendResponse):
    """Full sentiment analytics response including heatmap and mood distribution."""
    mood_distribution: dict[str, int]
    heatmap: list[HeatmapPoint]


# ============================================================================
# Psychology Module Schemas (v1.7)
# ============================================================================


class PersonalityTrait(BaseModel):
    """Single personality trait with score."""
    name: str  # curiosity, emotional_maturity, consistency, growth_mindset, resilience
    score: int  # 1-10
    description: str | None = None


class PersonalityProfile(BaseModel):
    """Personality profile response schema."""
    traits: dict[str, int]  # {trait_name: score}
    archetype: str  # e.g., "The Learner"
    confidence: float  # 0-100%
    insights: list[str]
    posts_analyzed: int
    assessment_date: str


class PsychologyAssessmentResponse(BaseModel):
    """Response schema for psychology assessment request."""
    success: bool
    assessment: PersonalityProfile | None = None
    error: str | None = None
    posts_available: int | None = None


class PsychologyProfileResponse(BaseModel):
    """Cached psychology profile response."""
    id: str
    traits: dict[str, int]
    archetype: str
    confidence_score: float
    insights: list[str]
    posts_analyzed_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}
