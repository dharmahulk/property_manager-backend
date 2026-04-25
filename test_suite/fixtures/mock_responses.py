"""Mock responses for API testing."""

from typing import Dict, Any


class MockResponse:
    """Mock HTTP response class."""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {}
    
    def json(self):
        return self.json_data
    
    @property
    def ok(self):
        return 200 <= self.status_code < 300


# Success responses
MOCK_USER_CREATED = MockResponse({
    "id": 1,
    "name": "Test User",
    "email": "test@example.com",
    "is_active": True
}, 200)

MOCK_USER_AUTHENTICATED = MockResponse({
    "id": 1,
    "name": "Test User", 
    "email": "test@example.com",
    "is_active": True
}, 200)

MOCK_USERS_LIST = MockResponse([
    {
        "id": 1,
        "name": "User One",
        "email": "user1@example.com",
        "is_active": True
    },
    {
        "id": 2,
        "name": "User Two",
        "email": "user2@example.com",
        "is_active": True
    }
], 200)

# Error responses
MOCK_USER_EXISTS = MockResponse({
    "detail": "Email already registered"
}, 400)

MOCK_INVALID_CREDENTIALS = MockResponse({
    "detail": "Invalid email or password"
}, 401)

MOCK_USER_NOT_FOUND = MockResponse({
    "detail": "User not found"
}, 404)

MOCK_VALIDATION_ERROR = MockResponse({
    "detail": [
        {
            "loc": ["body", "email"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}, 422)

MOCK_INTERNAL_SERVER_ERROR = MockResponse({
    "detail": "Internal server error"
}, 500)

# Demo mode responses
MOCK_DEMO_USER_CREATED = MockResponse({
    "id": 1,
    "name": "Demo User",
    "email": "demo@example.com",
    "is_active": True
}, 200)

MOCK_DEMO_USER_AUTHENTICATED = MockResponse({
    "id": 1,
    "name": "Demo User",
    "email": "demo@example.com", 
    "is_active": True
}, 200)
