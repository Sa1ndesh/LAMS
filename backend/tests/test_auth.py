import pytest
from datetime import timedelta
import jwt
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.schemas.auth import UserResponse


def test_hash_and_verify_password():
    """Test bcrypt password hashing and verification."""
    password = "MySecurePassword2026!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_creation_and_decoding():
    """Test JWT creation and payload decoding."""
    user_id = "usr-uuid-12345"
    role_name = "SUPER_ADMIN"

    token = create_access_token(subject=user_id, role=role_name)
    assert token is not None

    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["role"] == role_name
    assert "exp" in payload


def test_jwt_expiration():
    """Test that expired JWT tokens raise ExpiredSignatureError."""
    token = create_access_token(
        subject="usr-123",
        role="VIEWER",
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_user_response_schema_privacy():
    """Verify password_hash is never exposed in UserResponse schema."""
    schema_fields = UserResponse.model_fields.keys()
    assert "password" not in schema_fields
    assert "password_hash" not in schema_fields
    assert "hashed_password" not in schema_fields


@pytest.mark.asyncio
async def test_unauthenticated_protected_endpoint_returns_401():
    """Verify accessing protected endpoint without token returns HTTP 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/protected")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_invalid_bearer_token_returns_401():
    """Verify accessing protected endpoint with invalid token returns HTTP 401."""
    headers = {"Authorization": "Bearer invalid_malformed_token_123"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/protected", headers=headers)
        assert response.status_code == 401

