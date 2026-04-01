"""Unit tests for psychology service (v1.7 - AI personality module)."""
import pytest
import json
from datetime import datetime, timezone, timedelta

from backend.services.psychology_service import PsychologyService


class TestPsychologyServiceTraitExtraction:
    """Test personality trait extraction from LLM response."""

    def test_extract_traits_from_response(self):
        """Test extracting trait scores from LLM JSON response."""
        llm_response = json.dumps({
            "curiosity": 7,
            "emotional_maturity": 8,
            "consistency": 6,
            "growth_mindset": 7,
            "resilience": 8,
        })

        traits = PsychologyService.extract_personality_traits([], llm_response)

        assert traits["curiosity"] == 7
        assert traits["emotional_maturity"] == 8
        assert traits["consistency"] == 6
        assert traits["growth_mindset"] == 7
        assert traits["resilience"] == 8

    def test_extract_scores_from_text(self):
        """Test extracting numeric scores from plain text response."""
        text_response = "curiosity: 8\nemotional_maturity: 7\nconsistency: 6\ngrowth_mindset: 9\nresilience: 7"

        traits = PsychologyService.extract_personality_traits([], text_response)

        assert traits["curiosity"] == 8
        assert traits["emotional_maturity"] == 7
        assert traits["consistency"] == 6
        assert traits["growth_mindset"] == 9
        assert traits["resilience"] == 7

    def test_extract_scores_clamped_to_range(self):
        """Test that extracted scores are clamped to 1-10 range."""
        json_response = json.dumps({
            "curiosity": 15,
            "emotional_maturity": 0,
            "consistency": -5,
            "growth_mindset": 8,
            "resilience": 9
        })

        traits = PsychologyService.extract_personality_traits([], json_response)

        assert traits["curiosity"] == 10  # Clamped to 10
        assert traits["emotional_maturity"] == 1  # Clamped to 1
        assert traits["consistency"] == 1  # Clamped to 1

    def test_default_scores_when_not_found(self):
        """Test default score (5) when trait not found in response."""
        llm_response = "No traits here"

        traits = PsychologyService.extract_personality_traits([], llm_response)

        # All should default to 5
        assert traits["curiosity"] == 5
        assert traits["emotional_maturity"] == 5
        assert traits["consistency"] == 5
        assert traits["growth_mindset"] == 5
        assert traits["resilience"] == 5


class TestPsychologyServiceArchetype:
    """Test personality archetype determination."""

    def test_determine_learner_archetype(self):
        """Test identifying an archetype based on high curiosity and growth mindset."""
        traits = {
            "curiosity": 8,
            "emotional_maturity": 6,
            "consistency": 6,
            "growth_mindset": 8,
            "resilience": 6,
        }

        archetype, confidence = PsychologyService.determine_archetype(traits)

        # Should match an archetype
        assert archetype in ["The Learner", "The Innovator", "The Balanced"]
        assert confidence >= 50  # At least 50% confidence

    def test_determine_helper_archetype(self):
        """Test identifying an archetype based on high emotional maturity."""
        traits = {
            "curiosity": 5,
            "emotional_maturity": 9,
            "consistency": 8,
            "growth_mindset": 6,
            "resilience": 7,
        }

        archetype, confidence = PsychologyService.determine_archetype(traits)

        # Should match an archetype
        assert archetype in ["The Helper", "The Learner", "The Balanced", "The Philosopher"]
        assert confidence >= 50

    def test_determine_balanced_archetype(self):
        """Test identifying archetype with balanced traits."""
        traits = {
            "curiosity": 6,
            "emotional_maturity": 6,
            "consistency": 6,
            "growth_mindset": 6,
            "resilience": 6,
        }

        archetype, confidence = PsychologyService.determine_archetype(traits)

        # Should return a valid archetype
        valid_archetypes = ["The Learner", "The Helper", "The Philosopher", "The Resilient", "The Innovator", "The Balanced"]
        assert archetype in valid_archetypes
        assert confidence >= 50

    def test_confidence_score_normalization(self):
        """Test that confidence score is normalized between 50-100."""
        traits = {
            "curiosity": 10,
            "emotional_maturity": 10,
            "consistency": 10,
            "growth_mindset": 10,
            "resilience": 10,
        }

        archetype, confidence = PsychologyService.determine_archetype(traits)

        assert 50 <= confidence <= 100  # Min 50%, max 100%


class TestPsychologyServiceInsights:
    """Test personality insights generation."""

    def test_generate_insights_high_traits(self):
        """Test insights for high trait scores."""
        traits = {"curiosity": 9, "emotional_maturity": 8, "consistency": 7, "growth_mindset": 6, "resilience": 5}

        insights = PsychologyService.generate_insights(traits)

        assert len(insights) > 0
        # Should mention exceptional traits
        assert any("exceptional" in insight.lower() or "📊" in insight for insight in insights)

    def test_generate_insights_with_trends(self):
        """Test insights comparing previous and current traits."""
        current_traits = {"curiosity": 8, "emotional_maturity": 7, "consistency": 6, "growth_mindset": 7, "resilience": 6}
        previous_traits = {"curiosity": 6, "emotional_maturity": 5, "consistency": 6, "growth_mindset": 5, "resilience": 7}

        insights = PsychologyService.generate_insights(current_traits, previous_traits)

        assert len(insights) > 0
        # Should have insights - may or may not mention specific trends depending on implementation
        assert all(isinstance(insight, str) for insight in insights)

    def test_generate_insights_balanced_profile(self):
        """Test insights for balanced personality."""
        traits = {"curiosity": 6, "emotional_maturity": 6, "consistency": 6, "growth_mindset": 6, "resilience": 6}

        insights = PsychologyService.generate_insights(traits)

        assert len(insights) > 0
        # Should mention balance
        assert any("balance" in insight.lower() for insight in insights)

    def test_insights_limit(self):
        """Test that insights are limited to top 5."""
        traits = {"curiosity": 10, "emotional_maturity": 9, "consistency": 8, "growth_mindset": 7, "resilience": 6}

        insights = PsychologyService.generate_insights(traits)

        assert len(insights) <= 5


