"""Test data constants and factories."""

from typing import Dict, Any
from faker import Faker

fake = Faker()

# Valid test user data
VALID_USER_DATA = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password": "SecurePassword123!"
}

# Invalid test data scenarios
INVALID_USER_DATA = {
    "missing_name": {
        "email": "test@example.com",
        "password": "password123"
    },
    "missing_email": {
        "name": "Test User",
        "password": "password123"
    },
    "missing_password": {
        "name": "Test User",
        "email": "test@example.com"
    },
    "invalid_email": {
        "name": "Test User",
        "email": "invalid-email",
        "password": "password123"
    },
    "short_password": {
        "name": "Test User",
        "email": "test@example.com",
        "password": "123"
    },
    "empty_name": {
        "name": "",
        "email": "test@example.com",
        "password": "password123"
    }
}

# Mock database responses
MOCK_USER_RESPONSE = {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_active": True
}

# Authentication test data
AUTH_TEST_DATA = {
    "valid_login": {
        "email": "john.doe@example.com",
        "password": "SecurePassword123!"
    },
    "invalid_email": {
        "email": "nonexistent@example.com",
        "password": "SecurePassword123!"
    },
    "invalid_password": {
        "email": "john.doe@example.com",
        "password": "WrongPassword123!"
    },
    "empty_credentials": {
        "email": "",
        "password": ""
    }
}

# API response templates
API_RESPONSES = {
    "user_created": {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "is_active": True
    },
    "user_exists_error": {
        "detail": "Email already registered"
    },
    "invalid_credentials_error": {
        "detail": "Invalid email or password"
    },
    "validation_error": {
        "detail": [
            {
                "loc": ["body", "email"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
}


def generate_user_data(**overrides) -> Dict[str, Any]:
    """Generate random user data with optional overrides."""
    data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": fake.password(length=12)
    }
    data.update(overrides)
    return data


def generate_users(count: int = 5) -> list[Dict[str, Any]]:
    """Generate multiple user records."""
    return [generate_user_data() for _ in range(count)]


# Form data for UI testing
FORM_DATA = {
    "valid_signup": {
        "name": "Test User",
        "email": "test@example.com", 
        "password": "password123",
        "confirm_password": "password123",
        "terms": "on"
    },
    "mismatched_passwords": {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "confirm_password": "differentpassword",
        "terms": "on"
    },
    "terms_not_accepted": {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "confirm_password": "password123"
        # terms field missing
    }
}
