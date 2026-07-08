"""
Tests for the Mergington High School Activities API.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_list(self, client):
        """Test that GET /activities returns a list of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_chess_club_exists(self, client):
        """Test that Chess Club is in the activities"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data


class TestSignUpForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_duplicate_fails(self, client):
        """Test that duplicate signup fails"""
        email = "duplicate@mergington.edu"
        # First signup
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Second signup with same email should fail
        response = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "Already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup for nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_activity_full_fails(self, client):
        """Test that signup fails when activity is full"""
        # Get the current activity to find one that's nearly full
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Create a test activity scenario by making multiple signups
        # We'll use Basketball Club which has max 15 participants and only 1 current
        activity_name = "Basketball Club"
        max_participants = activities[activity_name]["max_participants"]
        current_count = len(activities[activity_name]["participants"])
        
        # Sign up enough people to fill the activity
        for i in range(max_participants - current_count):
            response = client.post(
                f"/activities/{activity_name}/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Next signup should fail
        response = client.post(
            f"/activities/{activity_name}/signup?email=fulltest@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "Activity is full" in data["detail"]

    def test_signup_updates_participant_count(self, client):
        """Test that signup updates the participant list"""
        activity_name = "Art Club"
        email = "artlover@mergington.edu"
        
        # Get initial count
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        # Signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Get updated count
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        participants = response_after.json()[activity_name]["participants"]
        
        assert count_after == count_before + 1
        assert email in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        activity_name = "Drama Club"
        email = "drama_test@mergington.edu"
        
        # First, signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering non-participant fails"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notaparticipant@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from nonexistent activity fails"""
        response = client.delete(
            "/activities/Fake Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_updates_participant_count(self, client):
        """Test that unregister updates the participant list"""
        activity_name = "Science Club"
        email = "science_test@mergington.edu"
        
        # Signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Get count before unregister
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        # Unregister
        client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        # Get count after unregister
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        participants = response_after.json()[activity_name]["participants"]
        
        assert count_after == count_before - 1
        assert email not in participants


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
