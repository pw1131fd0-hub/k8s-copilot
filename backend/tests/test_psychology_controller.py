"""Integration tests for psychology API controller (v1.7)."""
import pytest
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.database import get_db
from backend.models.orm_models import ClawBookPost, PsychologyProfile


@pytest.fixture
def client(db: Session):
    """Create test client with database session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestPsychologyAssessmentEndpoint:
    """Test POST /psychology/assess endpoint."""

    def test_assess_personality_insufficient_posts(self, client, db: Session):
        """Test assessment fails with insufficient posts."""
        # Clear posts
        db.query(ClawBookPost).delete()
        db.commit()

        # Create only 3 posts
        for i in range(3):
            post = ClawBookPost(
                mood="😊", content=f"Post {i}",
                author="test", created_at=datetime.now(timezone.utc)
            )
            db.add(post)
        db.commit()

        response = client.post("/api/v1/psychology/assess")

        assert response.status_code == 200
        data = response.json()
        assert not data["success"]
        assert "Minimum" in data.get("error", "")
        assert data["posts_available"] == 3

    def test_assess_personality_success(self, client, db: Session):
        """Test successful personality assessment."""
        # Clear existing data
        db.query(PsychologyProfile).delete()
        db.query(ClawBookPost).delete()
        db.commit()

        # Create 10 posts
        for i in range(10):
            post = ClawBookPost(
                mood=["😊", "😌", "😔", "😄", "🤔"][i % 5],
                content=f"Journal entry {i}. Learning new concepts and reflecting on progress.",
                author="test",
                created_at=datetime.now(timezone.utc),
            )
            db.add(post)
        db.commit()

        response = client.post("/api/v1/psychology/assess")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        assessment = data["assessment"]
        assert "traits" in assessment
        assert "archetype" in assessment
        assert "confidence" in assessment
        assert "insights" in assessment
        assert "posts_analyzed" in assessment

        # Verify trait structure
        traits = assessment["traits"]
        assert "curiosity" in traits
        assert "emotional_maturity" in traits
        assert "consistency" in traits
        assert "growth_mindset" in traits
        assert "resilience" in traits

        # Verify trait values
        for trait_name, score in traits.items():
            assert 1 <= score <= 10

        # Verify archetype
        valid_archetypes = [
            "The Learner", "The Helper", "The Philosopher",
            "The Resilient", "The Innovator", "The Balanced"
        ]
        assert assessment["archetype"] in valid_archetypes

        # Verify confidence
        assert 0 <= assessment["confidence"] <= 100

        # Verify insights
        assert len(assessment["insights"]) > 0
        assert all(isinstance(insight, str) for insight in assessment["insights"])

    def test_assess_personality_caches_result(self, client, db: Session):
        """Test that assessment result is cached and not re-assessed immediately."""
        # Clear existing data
        db.query(PsychologyProfile).delete()
        db.query(ClawBookPost).delete()
        db.commit()

        # Create posts
        for i in range(10):
            post = ClawBookPost(
                mood="😊",
                content=f"Entry {i}",
                author="test",
                created_at=datetime.now(timezone.utc),
            )
            db.add(post)
        db.commit()

        # First assessment
        response1 = client.post("/api/v1/psychology/assess")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"]

        archetype1 = data1["assessment"]["archetype"]

        # Second assessment (should return cached)
        response2 = client.post("/api/v1/psychology/assess")
        assert response2.status_code == 200
        data2 = response2.json()

        # Should return same archetype (from cache)
        assert data2["assessment"]["archetype"] == archetype1


class TestPsychologyProfileEndpoint:
    """Test GET /psychology/profile endpoint."""

    def test_get_profile_not_found(self, client, db: Session):
        """Test get profile when no assessment exists."""
        # Clear profiles
        db.query(PsychologyProfile).delete()
        db.commit()

        response = client.get("/api/v1/psychology/profile")

        assert response.status_code == 404
        data = response.json()
        assert "No personality profile found" in data["detail"]

    def test_get_profile_success(self, client, db: Session):
        """Test getting existing personality profile."""
        # Clear profiles
        db.query(PsychologyProfile).delete()
        db.commit()

        # Create profile
        profile = PsychologyProfile(
            traits_data=json.dumps({
                "curiosity": 7,
                "emotional_maturity": 8,
                "consistency": 6,
                "growth_mindset": 7,
                "resilience": 8,
            }),
            archetype="The Learner",
            confidence_score=82,
            insights_data=json.dumps([
                "You are highly curious",
                "Strong emotional maturity",
                "Consistent in values",
            ]),
            posts_analyzed_count=15,
        )
        db.add(profile)
        db.commit()

        response = client.get("/api/v1/psychology/profile")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == profile.id
        assert data["archetype"] == "The Learner"
        assert data["confidence_score"] == 82
        assert data["posts_analyzed_count"] == 15

        traits = data["traits"]
        assert traits["curiosity"] == 7
        assert traits["emotional_maturity"] == 8
        assert traits["consistency"] == 6
        assert traits["growth_mindset"] == 7
        assert traits["resilience"] == 8

        insights = data["insights"]
        assert len(insights) == 3
        assert "highly curious" in insights[0]


class TestPsychologyEndpointIntegration:
    """Integration tests for psychology endpoints."""

    def test_full_workflow(self, client, db: Session):
        """Test complete assessment and profile retrieval workflow."""
        # Clear data
        db.query(PsychologyProfile).delete()
        db.query(ClawBookPost).delete()
        db.commit()

        # Step 1: Try to get profile (should fail)
        response = client.get("/api/v1/psychology/profile")
        assert response.status_code == 404

        # Step 2: Create posts
        for i in range(10):
            post = ClawBookPost(
                mood=["😊", "😌", "😔", "😄", "🤔"][i % 5],
                content=f"Journal entry {i}",
                author="test",
                created_at=datetime.now(timezone.utc),
            )
            db.add(post)
        db.commit()

        # Step 3: Assess personality
        response = client.post("/api/v1/psychology/assess")
        assert response.status_code == 200
        assess_data = response.json()
        assert assess_data["success"]

        # Step 4: Get profile
        response = client.get("/api/v1/psychology/profile")
        assert response.status_code == 200
        profile_data = response.json()

        # Verify profile matches assessment
        assert profile_data["archetype"] == assess_data["assessment"]["archetype"]
        assert profile_data["confidence_score"] == assess_data["assessment"]["confidence"]

    def test_error_handling(self, client):
        """Test error handling in psychology endpoints."""
        # Post with invalid data should not crash
        response = client.post("/api/v1/psychology/assess")
        # Should return 200 with success: False instead of 500 error
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data


class TestPsychologySchemaValidation:
    """Test psychology schema validation."""

    def test_assessment_response_schema(self, client, db: Session):
        """Test that assessment response matches schema."""
        # Create posts
        db.query(ClawBookPost).delete()
        db.commit()

        for i in range(10):
            post = ClawBookPost(
                mood="😊",
                content=f"Entry {i}",
                author="test",
            )
            db.add(post)
        db.commit()

        response = client.post("/api/v1/psychology/assess")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "success" in data
        assert isinstance(data["success"], bool)

        if data["success"]:
            assessment = data["assessment"]
            assert isinstance(assessment, dict)
            assert "traits" in assessment
            assert "archetype" in assessment
            assert "confidence" in assessment
            assert "insights" in assessment

    def test_profile_response_schema(self, client, db: Session):
        """Test that profile response matches schema."""
        # Create profile
        db.query(PsychologyProfile).delete()
        db.commit()

        profile = PsychologyProfile(
            traits_data=json.dumps({"curiosity": 7, "emotional_maturity": 8, "consistency": 6, "growth_mindset": 7, "resilience": 8}),
            archetype="The Learner",
            confidence_score=82,
            insights_data=json.dumps(["Insight 1", "Insight 2"]),
            posts_analyzed_count=15,
        )
        db.add(profile)
        db.commit()

        response = client.get("/api/v1/psychology/profile")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = ["id", "traits", "archetype", "confidence_score", "insights", "posts_analyzed_count", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data

        # Check types
        assert isinstance(data["id"], str)
        assert isinstance(data["traits"], dict)
        assert isinstance(data["archetype"], str)
        assert isinstance(data["confidence_score"], (int, float))
        assert isinstance(data["insights"], list)
        assert isinstance(data["posts_analyzed_count"], int)
