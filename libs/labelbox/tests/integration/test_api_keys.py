import uuid
import pytest
import os

from labelbox.schema.timeunit import TimeUnit
from labelbox.schema.api_key import ApiKey


@pytest.mark.skipif(
    condition=os.environ["LABELBOX_TEST_ENVIRON"] != "prod",
    reason="Admin permissions are required to create API keys",
)
def test_create_api_key_success(client):
    # Create a test API key
    key_name = f"Test Key {uuid.uuid4()}"
    user_email = client.get_user().email

    assert (
        client.get_user().org_role().name == "Admin"
    ), "User must be an admin to create API keys"

    # Get available roles and use the first one
    available_roles = ApiKey._get_available_api_key_roles(client)
    assert (
        len(available_roles) > 0
    ), "No available roles found for API key creation"

    # Create the API key with a short validity period
    api_key_result = client.create_api_key(
        name=key_name,
        user=user_email,
        role=available_roles[0],
        validity=5,
        time_unit=TimeUnit.MINUTE,
    )

    # Verify the response format
    assert isinstance(
        api_key_result, dict
    ), "API key result should be a dictionary"
    assert "id" in api_key_result, "API key result should contain an 'id' field"
    assert (
        "jwt" in api_key_result
    ), "API key result should contain a 'jwt' field"

    # Verify the JWT token format (should be a JWT string)
    jwt = api_key_result["jwt"]
    assert isinstance(jwt, str), "JWT should be a string"
    assert jwt.count(".") == 2, "JWT should have three parts separated by dots"


def test_create_api_key_failed(client):
    # Test with invalid role
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=client.get_user().email,
            role="LABELER",  # This string should fail since role strings are case sensitive
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )
    assert "Invalid role specified" in str(excinfo.value)

    # Test with non-existent email
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user="test_labelbox@gmail.com",  # Non-existent email
            role="Admin",
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )
    assert "does not exist in the organization" in str(excinfo.value)

    # Test with maximum validity exceeded
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=client.get_user().email,
            role="Admin",
            validity=30,  # Beyond the 25 week maximum
            time_unit=TimeUnit.WEEK,
        )
    assert "Maximum validity period is 6 months" in str(excinfo.value)


def test_get_api_keys(client):
    """Test that we can retrieve API keys without creating new ones."""
    # Test getting all keys
    all_keys = client.get_api_keys()

    # Verify that we got a non-empty list of API keys
    assert len(all_keys) > 0, "Expected at least one API key to exist"

    # Verify that all returned items are ApiKey objects
    assert all(isinstance(key, ApiKey) for key in all_keys)


def test_create_api_key_invalid_role_formats(client):
    """Test that providing invalid role formats causes failure."""
    user_email = client.get_user().email

    # Test with misspelled role
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Lablr",  # Misspelled
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )
    assert "invalid role" in str(excinfo.value).lower()

    # Test with non-existent role
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="SuperAdmin",  # Non-existent role
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )
    assert "invalid role" in str(excinfo.value).lower()


def test_create_api_key_invalid_email_formats(client):
    """Test that providing invalid email formats causes failure."""
    # Test with random labelbox domain email that likely doesn't exist
    random_email = f"nonexistent_{uuid.uuid4()}@labelbox.com"

    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=random_email,
            role="Admin",
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )
    assert "does not exist in the organization" in str(excinfo.value).lower()

    # Test with malformed email
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user="not-an-email",
            role="Admin",
            validity=5,
            time_unit=TimeUnit.MINUTE,
        )
    assert "does not exist" in str(excinfo.value).lower()


def test_create_api_key_invalid_validity_values(client):
    """Test that providing invalid validity values causes failure."""
    user_email = client.get_user().email

    # Test with negative validity
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Admin",
            validity=-1,
            time_unit=TimeUnit.MINUTE,
        )
    assert "validity" in str(excinfo.value).lower()

    # Test with zero validity
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Admin",
            validity=0,
            time_unit=TimeUnit.MINUTE,
        )
    assert "minimum validity period is 1 minute" in str(excinfo.value).lower()

    # Days (exceeding 6 months)
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Admin",
            validity=185,  # Slightly over 6 months
            time_unit=TimeUnit.DAY,
        )
    assert "maximum validity" in str(excinfo.value).lower()

    # Test with validity period less than 1 minute
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Admin",
            validity=30,  # 30 seconds
            time_unit=TimeUnit.SECOND,
        )
    assert "Minimum validity period is 1 minute" in str(excinfo.value)


def test_create_api_key_invalid_time_unit(client):
    """Test that providing invalid time unit causes failure."""
    user_email = client.get_user().email

    # Test with None time unit
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Admin",
            validity=5,
            time_unit=None,
        )
    assert "time_unit must be a valid TimeUnit enum value" in str(excinfo.value)

    # Test with invalid string instead of TimeUnit enum
    # Note: This also raises ValueError, not TypeError
    with pytest.raises(ValueError) as excinfo:
        client.create_api_key(
            name=f"Test Key {uuid.uuid4()}",
            user=user_email,
            role="Admin",
            validity=5,
            time_unit="days",  # String instead of TimeUnit enum
        )
    assert "valid TimeUnit" in str(excinfo.value)
