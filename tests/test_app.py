import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Import the app and related functions
from src.app import app, activities, load_activities, save_activities, activities_file

# Default activities data for resetting
DEFAULT_ACTIVITIES = {
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
        "description": "Competitive basketball practice and games",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["alex@mergington.edu"]
    },
    "Tennis Club": {
        "description": "Learn tennis skills and play matches",
        "schedule": "Saturdays, 10:00 AM - 12:00 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "grace@mergington.edu"]
    },
    "Art Studio": {
        "description": "Explore painting, drawing, and sculpture",
        "schedule": "Tuesdays and Thursdays, 4:30 PM - 6:00 PM",
        "max_participants": 16,
        "participants": []
    },
    "Debate Club": {
        "description": "Practice public speaking and debate skills",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": []
    },
    "Science Club": {
        "description": "Conduct experiments and learn about scientific concepts",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 22,
        "participants": []
    },
    "Music Band": {
        "description": "Learn to play instruments and perform music",
        "schedule": "Tuesdays, 5:00 PM - 6:30 PM",
        "max_participants": 20,
        "participants": []
    }
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client with isolated file storage"""
    # Set activities_file to temp path
    test_file = tmp_path / "activities.json"
    monkeypatch.setattr('src.app.activities_file', test_file)
    
    # Reset activities to default
    activities.clear()
    activities.update(DEFAULT_ACTIVITIES)
    
    # If test file exists, load it; else use default
    load_activities()
    
    yield TestClient(app)


def test_get_activities(client):
    """Test GET /activities returns all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # All activities
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_root_redirect(client):
    """Test GET / redirects to static file"""
    response = client.get("/", allow_redirects=False)
    assert response.status_code == 307  # Redirect
    assert "/static/index.html" in response.headers["location"]


def test_signup_success(client):
    """Test successful signup"""
    response = client.post("/activities/Art%20Studio/signup?email=test@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert "Signed up test@mergington.edu for Art Studio" in data["message"]
    
    # Verify in activities
    response = client.get("/activities")
    data = response.json()
    assert "test@mergington.edu" in data["Art Studio"]["participants"]


def test_signup_duplicate(client):
    """Test signup with already enrolled student"""
    # First signup
    client.post("/activities/Art%20Studio/signup?email=test@mergington.edu")
    
    # Duplicate signup
    response = client.post("/activities/Art%20Studio/signup?email=test@mergington.edu")
    assert response.status_code == 400
    data = response.json()
    assert "Student is already signed up" in data["detail"]


def test_signup_nonexistent_activity(client):
    """Test signup for nonexistent activity"""
    response = client.post("/activities/Nonexistent/signup?email=test@mergington.edu")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_unregister_success(client):
    """Test successful unregister"""
    # First signup
    client.post("/activities/Art%20Studio/signup?email=test@mergington.edu")
    
    # Then unregister
    response = client.delete("/activities/Art%20Studio/signup?email=test@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered test@mergington.edu from Art Studio" in data["message"]
    
    # Verify removed
    response = client.get("/activities")
    data = response.json()
    assert "test@mergington.edu" not in data["Art Studio"]["participants"]


def test_unregister_not_enrolled(client):
    """Test unregister for student not enrolled"""
    response = client.delete("/activities/Art%20Studio/signup?email=notenrolled@mergington.edu")
    assert response.status_code == 400
    data = response.json()
    assert "Student is not signed up" in data["detail"]


def test_unregister_nonexistent_activity(client):
    """Test unregister for nonexistent activity"""
    response = client.delete("/activities/Nonexistent/signup?email=test@mergington.edu")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_persistence_signup(client, tmp_path):
    """Test that signup persists to JSON file"""
    client.post("/activities/Art%20Studio/signup?email=persist@mergington.edu")
    
    # Check file was created/updated
    test_file = tmp_path / "activities.json"
    assert test_file.exists()
    
    with open(test_file, 'r') as f:
        saved_data = json.load(f)
    
    assert "persist@mergington.edu" in saved_data["Art Studio"]["participants"]


def test_persistence_unregister(client, tmp_path):
    """Test that unregister persists to JSON file"""
    # Signup first
    client.post("/activities/Art%20Studio/signup?email=persist@mergington.edu")
    
    # Unregister
    client.delete("/activities/Art%20Studio/signup?email=persist@mergington.edu")
    
    # Check file
    test_file = tmp_path / "activities.json"
    with open(test_file, 'r') as f:
        saved_data = json.load(f)
    
    assert "persist@mergington.edu" not in saved_data["Art Studio"]["participants"]