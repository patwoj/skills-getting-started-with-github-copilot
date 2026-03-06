# tests/test_app.py
"""
Comprehensive test suite for Mergington High School API

Tests cover all endpoints with success scenarios, error cases, and edge cases.
Uses pytest with FastAPI's TestClient for synchronous testing.
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """Provide a fresh copy of activities to avoid test pollution."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team practices and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis lessons and competitive matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["ava@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater performances, scriptwriting, and acting workshops",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu", "noah@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and sculpture projects",
            "schedule": "Mondays and Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 18,
            "participants": ["mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking competitions",
            "schedule": "Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 10,
            "participants": ["liam@mergington.edu", "charlotte@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore STEM topics",
            "schedule": "Fridays, 4:00 PM - 5:00 PM",
            "max_participants": 22,
            "participants": ["alexander@mergington.edu"]
        }
    }


@pytest.fixture(autouse=True)
def reset_activities(fresh_activities):
    """Reset activities before each test to ensure test isolation."""
    # Clear and repopulate the activities dictionary
    activities.clear()
    activities.update(fresh_activities)
    yield


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns a 200 status code."""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary."""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_all_activities(self, client):
        """Test that all activities are returned."""
        response = client.get("/activities")
        data = response.json()

        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club"
        ]

        for activity in expected_activities:
            assert activity in data

    def test_get_activities_includes_required_fields(self, client):
        """Test that each activity contains required fields."""
        response = client.get("/activities")
        data = response.json()

        required_fields = ["description", "schedule", "max_participants", "participants"]

        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in activity '{activity_name}'"

    def test_get_activities_participants_is_list(self, client):
        """Test that participants are returned as a list."""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for '{activity_name}' should be a list"

    def test_get_activities_consistency(self, client):
        """Test that multiple calls return consistent data."""
        response1 = client.get("/activities")
        response2 = client.get("/activities")

        assert response1.json() == response2.json()


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "student@mergington.edu"}
        )

        assert response.status_code == 200
        assert "message" in response.json()
        assert "Chess Club" in response.json()["message"]
        assert "student@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity."""
        email = "newstudent@mergington.edu"
        client.post("/activities/Drama Club/signup", params={"email": email})

        # Verify via GET
        response = client.get("/activities")
        assert email in response.json()["Drama Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity."""
        response = client.post(
            "/activities/Non Existent Club/signup",
            params={"email": "student@mergington.edu"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered."""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )

        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_duplicate_prevention_multiple_attempts(self, client):
        """Test that attempting to signup twice is prevented."""
        email = "student@mergington.edu"

        # First signup should succeed
        response1 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_different_activities(self, client):
        """Test that a student can signup for multiple different activities."""
        email = "versatile@mergington.edu"

        activities_to_join = ["Chess Club", "Art Studio", "Science Club"]

        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify signup in all activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities_to_join:
            assert email in data[activity]["participants"]

    def test_signup_email_parameter(self, client):
        """Test that email parameter is required."""
        response = client.post("/activities/Chess Club/signup")
        # Missing parameter should result in validation error
        assert response.status_code in [422, 400]

    def test_signup_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive."""
        response = client.post(
            "/activities/chess club/signup",  # lowercase
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404

    def test_signup_whitespace_handling(self, client):
        """Test signup with activity names containing spaces."""
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": "coder@mergington.edu"}
        )
        assert response.status_code == 200

    def test_signup_capacity_management(self, client):
        """Test that participants list grows correctly with each signup."""
        activity_name = "Basketball Team"

        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])

        # Add new participant
        email = "newplayer@mergington.edu"
        client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Verify count increased
        response = client.get("/activities")
        new_count = len(response.json()[activity_name]["participants"])
        assert new_count == initial_count + 1

    def test_signup_various_email_formats(self, client):
        """Test signup with various valid email formats."""
        emails = [
            "simple@example.com",
            "user.name@example.co.uk",
            "test+tag@example.org",
            "123@example.com"
        ]

        for email in emails:
            response = client.post(
                "/activities/Art Studio/signup",
                params={"email": email}
            )
            assert response.status_code == 200, f"Failed for email: {email}"


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        # michael@mergington.edu is in Chess Club
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )

        assert response.status_code == 200
        assert "message" in response.json()
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant."""
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/unregister", params={"email": email})

        # Verify via GET
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity."""
        response = client.delete(
            "/activities/Non Existent Club/unregister",
            params={"email": "student@mergington.edu"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_not_registered(self, client):
        """Test unregister when student is not registered."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "never.registered@mergington.edu"}
        )

        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_double_unregister_prevention(self, client):
        """Test that double unregister is prevented."""
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # First unregister should succeed
        response1 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Second unregister should fail
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "not signed up" in response2.json()["detail"].lower()

    def test_unregister_then_signup_again(self, client):
        """Test that a student can re-signup after unregistering."""
        email = "flexible@mergington.edu"
        activity = "Drama Club"

        # Sign up initially
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Unregister
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200

        # Re-signup
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200

        # Verify they're signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

    def test_unregister_email_parameter(self, client):
        """Test that email parameter is required."""
        response = client.delete("/activities/Chess Club/unregister")
        assert response.status_code in [422, 400]

    def test_unregister_does_not_affect_other_participants(self, client):
        """Test that unregistering one student doesn't affect others."""
        activity = "Chess Club"
        email_to_remove = "michael@mergington.edu"

        # Get all participants before
        response = client.get("/activities")
        participants_before = response.json()[activity]["participants"].copy()

        # Unregister one student
        client.delete(f"/activities/{activity}/unregister", params={"email": email_to_remove})

        # Get all participants after
        response = client.get("/activities")
        participants_after = response.json()[activity]["participants"]

        # Verify only the target was removed
        assert len(participants_after) == len(participants_before) - 1

        for participant in participants_after:
            assert participant != email_to_remove
            assert participant in participants_before

    def test_unregister_all_participants_sequentially(self, client):
        """Test unregistering all participants from an activity."""
        activity = "Programming Class"

        # Get current participants
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"].copy()

        # Unregister each participant
        for email in initial_participants:
            response = client.delete(
                f"/activities/{activity}/unregister",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify activity is empty
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == 0


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""

    def test_full_lifecycle_signup_and_unregister(self, client):
        """Test complete lifecycle: signup then unregister."""
        email = "lifecycle@mergington.edu"
        activity = "Debate Team"

        # Initial check - not registered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Verify registered
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_students_concurrent_signups(self, client):
        """Test multiple students signing up for the same activity."""
        activity = "Science Club"
        emails = [
            "student1@example.com",
            "student2@example.com",
            "student3@example.com",
            "student4@example.com"
        ]

        # All students sign up
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants

    def test_student_activity_management_workflow(self, client):
        """Test a realistic student workflow across multiple activities."""
        email = "busy_student@mergington.edu"
        activities_list = ["Chess Club", "Art Studio", "Science Club"]

        # Sign up for multiple activities
        for activity in activities_list:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Drop one activity
        client.delete(
            "/activities/Art Studio/unregister",
            params={"email": email}
        )

        # Sign up for another
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response.status_code == 200

        # Verify final state
        response = client.get("/activities")
        data = response.json()

        # Verify still registered for Chess Club and Science Club
        assert email in data["Chess Club"]["participants"]
        assert email in data["Science Club"]["participants"]

        # Verify registered for Basketball Team
        assert email in data["Basketball Team"]["participants"]


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_400_errors_have_detail_message(self, client):
        """Test that 400 errors include detail messages."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_404_errors_have_detail_message(self, client):
        """Test that 404 errors include detail messages."""
        response = client.post(
            "/activities/Nonexistent/signup",
            params={"email": "test@example.com"}
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_response_messages_are_descriptive(self, client):
        """Test that success messages contain activity name and email."""
        email = "descriptive@example.com"
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )

        json_response = response.json()
        assert email in json_response["message"]
        assert "Tennis Club" in json_response["message"]

    def test_special_characters_in_email(self, client):
        """Test handling of special characters in email."""
        email = "user+test@example.com"
        response = client.post(
            "/activities/Gym Class/signup",
            params={"email": email}
        )

        assert response.status_code == 200

    def test_empty_string_email(self, client):
        """Test handling of empty email string."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        # Should either accept or reject with proper error
        assert response.status_code in [200, 400, 422]

    def test_activity_data_integrity_after_operations(self, client):
        """Test that activity data structure remains intact after operations."""
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Perform various operations
        client.post("/activities/Chess Club/signup", params={"email": "new@example.com"})
        client.delete("/activities/Drama Club/unregister", params={"email": "isabella@mergington.edu"})

        # Verify data structure
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data
                assert activity_data[field] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])