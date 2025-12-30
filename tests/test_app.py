"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original participants
    original_participants = {
        name: details["participants"].copy()
        for name, details in activities.items()
    }
    yield
    # Restore original participants after test
    for name, details in activities.items():
        details["participants"] = original_participants[name]


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that getting activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_fields(self, client):
        """Test that each activity has the expected fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for name, details in activities_data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_registration(self, client):
        """Test that signing up twice returns an error"""
        # First signup
        client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        # Second signup with same email
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up"

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the list"""
        email = "verification@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email in participants


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First sign up
        email = "tounregister@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self, client):
        """Test unregister when not signed up returns 400"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "toremove@mergington.edu"
        # Sign up first
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        # Verify added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]


class TestRootRedirect:
    """Tests for the root endpoint redirect"""

    def test_root_redirects_to_index(self, client):
        """Test that root path redirects to the static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
