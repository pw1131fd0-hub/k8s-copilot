"""Psychology service for ClawBook v1.7 - AI personality profile assessment and tracking."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json
import re

from backend.models.orm_models import ClawBookPost, PsychologyProfile
from backend.models.schemas import (
    PersonalityTrait,
    PersonalityProfile as PersonalityProfileSchema,
    PsychologyAssessmentResponse,
)


class PsychologyService:
    """Service for analyzing AI personality based on journal entries."""

    # Personality archetypes
    ARCHETYPES = {
        "The Learner": {"curiosity_min": 7, "growth_mindset_min": 7, "emotional_maturity_min": 5},
        "The Helper": {"emotional_maturity_min": 8, "consistency_min": 7, "resilience_min": 6},
        "The Philosopher": {"curiosity_min": 8, "consistency_min": 7, "emotional_maturity_min": 7},
        "The Resilient": {"resilience_min": 8, "growth_mindset_min": 7, "consistency_min": 6},
        "The Innovator": {"curiosity_min": 8, "growth_mindset_min": 8, "emotional_maturity_min": 5},
        "The Balanced": {"curiosity_min": 6, "emotional_maturity_min": 6, "consistency_min": 6, "growth_mindset_min": 6, "resilience_min": 6},
    }

    @classmethod
    def extract_personality_traits(cls, posts: List[ClawBookPost], llm_response: str) -> Dict[str, int]:
        """
        Extract personality trait scores from LLM response.

        Args:
            posts: List of posts to analyze
            llm_response: LLM response text (JSON or plain text)

        Returns:
            Dictionary with trait scores (1-10 each)
        """
        # Try to parse as JSON first
        try:
            data = json.loads(llm_response)
            traits = {
                "curiosity": max(1, min(10, int(data.get("curiosity", 5)))),
                "emotional_maturity": max(1, min(10, int(data.get("emotional_maturity", 5)))),
                "consistency": max(1, min(10, int(data.get("consistency", 5)))),
                "growth_mindset": max(1, min(10, int(data.get("growth_mindset", 5)))),
                "resilience": max(1, min(10, int(data.get("resilience", 5)))),
            }
            return traits
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # Fall back to text parsing

        # Parse as plain text
        traits = {
            "curiosity": cls._extract_score_from_response(llm_response, "curiosity", 5),
            "emotional_maturity": cls._extract_score_from_response(llm_response, "emotional_maturity", 5),
            "consistency": cls._extract_score_from_response(llm_response, "consistency", 5),
            "growth_mindset": cls._extract_score_from_response(llm_response, "growth_mindset", 5),
            "resilience": cls._extract_score_from_response(llm_response, "resilience", 5),
        }
        return traits

    @classmethod
    def _extract_score_from_response(cls, text: str, trait: str, default: int = 5) -> int:
        """
        Extract a numeric score (1-10) from text for a given trait.

        Args:
            text: Text to search
            trait: Trait name
            default: Default score if not found

        Returns:
            Score between 1 and 10
        """
        # Look for patterns like "curiosity: 7" or "curiosity score: 8"
        pattern = rf"{trait}\s*(?:score)?:?\s*(\d+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            return max(1, min(10, score))  # Clamp to 1-10
        return default

    @classmethod
    def determine_archetype(cls, traits: Dict[str, int]) -> tuple[str, float]:
        """
        Determine personality archetype based on trait scores.

        Args:
            traits: Dictionary of trait scores

        Returns:
            Tuple of (archetype_name, confidence_score)
        """
        best_archetype = "The Balanced"
        best_score = 0.0

        for archetype_name, requirements in cls.ARCHETYPES.items():
            # Calculate how well traits match this archetype
            matches = 0
            total_requirements = len(requirements)

            for trait_name, min_value in requirements.items():
                if traits.get(trait_name, 5) >= min_value:  # Default to 5 if not found
                    matches += 1

            match_percentage = (matches / total_requirements) * 100
            if match_percentage > best_score:
                best_score = match_percentage
                best_archetype = archetype_name

        # Confidence is the match percentage (0-100%)
        # For perfect matches, confidence should be high
        confidence = max(50, best_score)  # Minimum 50% confidence
        return best_archetype, confidence

    @classmethod
    def generate_insights(cls, traits: Dict[str, int], previous_traits: Optional[Dict[str, int]] = None) -> List[str]:
        """
        Generate personality insights based on current and previous traits.

        Args:
            traits: Current trait scores
            previous_traits: Previous trait scores for comparison

        Returns:
            List of insight strings
        """
        insights = []

        # High/low trait insights
        for trait_name, score in traits.items():
            if score >= 8:
                insights.append(f"🌟 You show exceptional {trait_name.replace('_', ' ')} ({score}/10)")
            elif score <= 3:
                insights.append(f"📈 Consider developing your {trait_name.replace('_', ' ')} ({score}/10)")

        # Trend insights if previous data available
        if previous_traits:
            for trait_name, current_score in traits.items():
                previous_score = previous_traits.get(trait_name, 5)
                change = current_score - previous_score
                if change > 2:
                    insights.append(f"📊 Your {trait_name.replace('_', ' ')} increased {change} points")
                elif change < -2:
                    insights.append(f"📊 Your {trait_name.replace('_', ' ')} decreased {abs(change)} points")

        # Balance insights
        all_scores = list(traits.values())
        if max(all_scores) - min(all_scores) > 5:
            insights.append("⚖️  Consider balancing your strengths with development areas")
        elif max(all_scores) - min(all_scores) <= 2:
            insights.append("✨ You maintain a well-balanced personality profile")

        # Add a custom insight
        insights.append("💡 Regular journaling helps refine self-understanding")

        return insights[:5]  # Return top 5 insights

    @classmethod
    def assess_personality(
        cls,
        db: Session,
        llm_response: str,
        min_posts: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform personality assessment based on journal entries.

        Args:
            db: Database session
            llm_response: LLM response with personality analysis
            min_posts: Minimum posts required for assessment

        Returns:
            Dictionary with assessment results
        """
        # Get recent posts
        posts = (
            db.query(ClawBookPost)
            .order_by(desc(ClawBookPost.created_at))
            .limit(50)
            .all()
        )

        if len(posts) < min_posts:
            return {
                "success": False,
                "error": f"Minimum {min_posts} journal entries required for personality assessment",
                "posts_available": len(posts),
            }

        # Extract trait scores from LLM response
        traits = cls.extract_personality_traits(posts, llm_response)

        # Determine archetype
        archetype_name, confidence = cls.determine_archetype(traits)

        # Generate insights
        insights = cls.generate_insights(traits)

        # Get previous profile for trend comparison
        previous_profile = (
            db.query(PsychologyProfile)
            .order_by(desc(PsychologyProfile.created_at))
            .first()
        )

        previous_traits = {}
        if previous_profile and previous_profile.traits_data:
            previous_traits = json.loads(previous_profile.traits_data)

        # Create assessment result
        assessment = {
            "traits": traits,
            "archetype": archetype_name,
            "confidence": confidence,
            "insights": insights,
            "posts_analyzed": len(posts),
            "assessment_date": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "success": True,
            "assessment": assessment,
        }

    @classmethod
    def save_profile(cls, db: Session, assessment: Dict[str, Any]) -> PsychologyProfile:
        """
        Save personality profile to database.

        Args:
            db: Database session
            assessment: Assessment data

        Returns:
            Saved PsychologyProfile instance
        """
        profile = PsychologyProfile(
            traits_data=json.dumps(assessment["traits"]),
            archetype=assessment["archetype"],
            confidence_score=assessment["confidence"],
            insights_data=json.dumps(assessment["insights"]),
            posts_analyzed_count=assessment["posts_analyzed"],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @classmethod
    def get_latest_profile(cls, db: Session) -> Optional[PsychologyProfile]:
        """
        Get the latest saved personality profile.

        Args:
            db: Database session

        Returns:
            Latest PsychologyProfile or None
        """
        return (
            db.query(PsychologyProfile)
            .order_by(desc(PsychologyProfile.created_at))
            .first()
        )

    @classmethod
    def profile_needs_update(cls, db: Session, hours: int = 168) -> bool:
        """
        Check if profile needs update (e.g., weekly).

        Args:
            db: Database session
            hours: Hours since last update (default: 1 week = 168 hours)

        Returns:
            True if profile is stale and needs update
        """
        latest = cls.get_latest_profile(db)
        if not latest:
            return True

        age = datetime.now(timezone.utc) - latest.created_at
        return age > timedelta(hours=hours)
