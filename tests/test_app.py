import os
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_pocketsmart.sqlite"
os.environ["SECRET_KEY"] = "test-secret"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login(email="test@example.com"):
    client.get("/register")
    r = client.post("/register", data={"name": "Test User", "email": email, "password": "test1234"}, follow_redirects=False)
    assert r.status_code == 303
    return r.headers["set-cookie"]


def test_health_and_startup():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/startup").json()["status"] == "ready"


def test_public_pages():
    assert client.get("/").status_code == 200
    assert client.get("/register").status_code == 200
    assert client.get("/login").status_code == 200


def test_protected_pages_require_login():
    assert client.get("/dashboard").status_code == 401
    assert client.get("/history").status_code == 401
    assert client.get("/planner/home").status_code == 401


def test_register_login_and_session():
    email = "user1@example.com"
    r = client.post("/register", data={"name": "User One", "email": email, "password": "test1234"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/dashboard"
    info = client.get("/session-info").json()
    assert info["logged_in"] is True
    assert client.get("/dashboard").status_code == 200


def test_home_party_jewelry_generation_and_history():
    # Register a fresh user and keep its cookie in the same client.
    client.get("/logout")
    register_and_login("user2@example.com")

    home = client.post("/generate-home", data={"budget": 50000, "room_type": "Living Room", "style": "Modern", "items": "Sofa, lights", "location": "Chennai"})
    assert home.status_code == 200
    assert "Recommendations" in home.text

    party = client.post("/generate-party", data={"budget": 30000, "guests": 30, "event_type": "Birthday", "venue": "Restaurant", "city": "Chennai"})
    assert party.status_code == 200
    assert "Birthday" in party.text

    jewelry = client.post("/generate-jewelry", data={"budget": 20000, "occasion": "Wedding", "style": "Elegant", "outfit_notes": "Blue dress"})
    assert jewelry.status_code == 200
    assert "jewelry" in jewelry.text.lower()

    history = client.get("/history")
    assert history.status_code == 200
    assert history.text.count("View plan") >= 1

    session = client.get("/session-data").json()
    assert session["recommendation_count"] >= 3


def test_token_endpoint():
    client.get("/logout")
    register_and_login("token@example.com")
    r = client.post("/token", data={"email": "token@example.com", "password": "test1234"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
