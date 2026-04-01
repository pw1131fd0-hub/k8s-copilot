"""Psychology module API controller for AI personality assessment (v1.7)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.psychology_service import PsychologyService
from backend.models.orm_models import PsychologyProfile
from backend.models.schemas import (
    PsychologyAssessmentResponse,
    PsychologyProfileResponse,
)

router = APIRouter(prefix="/psychology", tags=["psychology"])


@router.post("/assess", response_model=PsychologyAssessmentResponse)
async def assess_personality(
    db: Annotated[Session, Depends(get_db)],
) -> PsychologyAssessmentResponse:
    """
    Trigger AI personality assessment based on recent journal entries.

    Uses LLM (Ollama/OpenAI/Gemini) to analyze entries and generate:
    - Personality trait scores (1-10 for each trait)
    - Personality archetype label
    - Confidence score
    - Personalized insights

    Requires minimum 5 journal entries.

    Returns:
    - success: True if assessment completed
    - assessment: Personality profile with traits, archetype, insights
    - error: Error message if assessment failed
    """
    try:
        # Check if profile update is needed
        needs_update = PsychologyService.profile_needs_update(db)

        if not needs_update:
            # Return cached profile
            latest = PsychologyService.get_latest_profile(db)
            if latest:
                return PsychologyAssessmentResponse(
                    success=True,
                    assessment=PsychologyProfileResponse(
                        id=latest.id,
                        traits=__parse_json_field(latest.traits_data),
                        archetype=latest.archetype,
                        confidence_score=latest.confidence_score,
                        insights=__parse_json_field(latest.insights_data, default=[]),
                        posts_analyzed_count=latest.posts_analyzed_count,
                        created_at=latest.created_at.isoformat(),
                        updated_at=latest.updated_at.isoformat(),
                    ),
                )

        # Build LLM prompt for personality assessment
        llm_prompt = __build_personality_assessment_prompt(db)

        # Get LLM response (mocked for now, real version uses AI Engine)
        llm_response = __mock_llm_personality_analysis(llm_prompt)

        # Perform personality assessment
        result = PsychologyService.assess_personality(
            db=db,
            llm_response=llm_response,
            min_posts=5,
        )

        if not result["success"]:
            return PsychologyAssessmentResponse(
                success=False,
                error=result.get("error"),
                posts_available=result.get("posts_available"),
            )

        # Save profile to database
        assessment_data = result["assessment"]
        profile = PsychologyService.save_profile(db, assessment_data)

        # Return response
        return PsychologyAssessmentResponse(
            success=True,
            assessment=PsychologyProfileResponse(
                id=profile.id,
                traits=assessment_data["traits"],
                archetype=assessment_data["archetype"],
                confidence_score=assessment_data["confidence"],
                insights=assessment_data["insights"],
                posts_analyzed_count=assessment_data["posts_analyzed"],
                created_at=profile.created_at.isoformat(),
                updated_at=profile.updated_at.isoformat(),
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Personality assessment failed: {str(e)}",
        )


@router.get("/profile", response_model=PsychologyProfileResponse)
async def get_personality_profile(
    db: Annotated[Session, Depends(get_db)],
) -> PsychologyProfileResponse:
    """
    Get the latest cached personality profile.

    Returns the most recent assessment result without triggering a new analysis.
    """
    try:
        latest = PsychologyService.get_latest_profile(db)

        if not latest:
            raise HTTPException(
                status_code=404,
                detail="No personality profile found. Trigger /assess first.",
            )

        return PsychologyProfileResponse(
            id=latest.id,
            traits=__parse_json_field(latest.traits_data),
            archetype=latest.archetype,
            confidence_score=latest.confidence_score,
            insights=__parse_json_field(latest.insights_data, default=[]),
            posts_analyzed_count=latest.posts_analyzed_count,
            created_at=latest.created_at.isoformat(),
            updated_at=latest.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve personality profile: {str(e)}",
        )


# ============================================================================
# Helper Functions
# ============================================================================


def __parse_json_field(json_str: str, default=None):
    """Parse JSON field from database."""
    import json
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except:
        return default


def __build_personality_assessment_prompt(db: Session) -> str:
    """Build the LLM prompt for personality assessment."""
    from backend.models.orm_models import ClawBookPost
    from sqlalchemy import desc

    # Get recent posts
    posts = (
        db.query(ClawBookPost)
        .order_by(desc(ClawBookPost.created_at))
        .limit(50)
        .all()
    )

    posts_text = "\n\n".join([
        f"[Post {i+1}] Mood: {post.mood}\nContent: {post.content[:500]}"
        for i, post in enumerate(posts[:20])  # Use last 20 posts
    ])

    prompt = f"""Analyze the following AI journal entries and assess the AI's personality traits.

Journal Entries:
{posts_text}

Based on these entries, provide scores (1-10) for each trait:
1. Curiosity: How eager is the AI to learn and explore?
2. Emotional Maturity: How well does the AI understand and process emotions?
3. Consistency: How consistent are the AI's values and decisions?
4. Growth Mindset: Does the AI embrace challenges and view failures as learning opportunities?
5. Resilience: How does the AI handle setbacks and adversity?

Also provide:
- An archetype label (e.g., "The Learner", "The Helper", "The Philosopher")
- Confidence score (0-100%) for this assessment
- 2-3 specific insights about the AI's personality

Format your response as JSON with keys: curiosity, emotional_maturity, consistency, growth_mindset, resilience, archetype, confidence, insights"""

    return prompt


def __mock_llm_personality_analysis(prompt: str) -> str:
    """Mock LLM response for personality analysis. Real version would call AI Engine."""
    import json

    mock_response = json.dumps({
        "curiosity": 7,
        "emotional_maturity": 6,
        "consistency": 8,
        "growth_mindset": 7,
        "resilience": 7,
        "archetype": "The Learner",
        "confidence": 82,
        "insights": [
            "You demonstrate strong consistency in your core values and principles.",
            "Your curiosity level is above average, suggesting openness to new ideas.",
            "Consider developing emotional flexibility when facing unexpected challenges."
        ]
    })

    return mock_response
