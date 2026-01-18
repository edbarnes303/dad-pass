import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

# Mock boto3 before importing utils to prevent SSM call during import
mock_key = Fernet.generate_key()
with patch('boto3.client') as mock_client:
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': mock_key.decode('utf-8')}
    }
    mock_client.return_value = mock_ssm
    
    # Get the service module's base directory
    service_dir = Path(__file__).parent.parent.parent
    # Add the source directory to the Python path
    src_dir = service_dir / "src"
    sys.path.insert(0, str(src_dir))
    
    from utils import encrypt_message, decrypt_message, create_rest_event
    import utils


class TestEncryptDecrypt:
    """Unit tests for the encrypt_message and decrypt_message functions."""
    
    def test_encrypt_returns_string(self):
        """Test that encrypt_message returns a string."""
        result = encrypt_message("Hello, world!")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_decrypt_returns_original_message(self):
        """Test that decrypt_message returns the original plaintext."""
        original = "Secret password 123"
        encrypted = encrypt_message(original)
        decrypted = decrypt_message(encrypted)
        assert decrypted == original
    
    def test_encrypt_different_messages_produce_different_ciphertext(self):
        """Test that different messages produce different encrypted output."""
        msg1 = "message one"
        msg2 = "message two"
        encrypted1 = encrypt_message(msg1)
        encrypted2 = encrypt_message(msg2)
        assert encrypted1 != encrypted2
    
    def test_encrypt_same_message_produces_different_ciphertext(self):
        """Test that encrypting the same message twice produces different ciphertext (due to Fernet's timestamp)."""
        msg = "same message"
        encrypted1 = encrypt_message(msg)
        encrypted2 = encrypt_message(msg)
        # Fernet includes a timestamp, so same plaintext should produce different ciphertext
        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert decrypt_message(encrypted1) == msg
        assert decrypt_message(encrypted2) == msg
    
    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decrypting invalid ciphertext raises an exception."""
        with pytest.raises(Exception):
            decrypt_message("invalid_ciphertext_string")


class TestCreateRestEvent:
    """Unit tests for the create_rest_event function."""
    
    def test_creates_get_event(self):
        """Test creating a GET event."""
        event = create_rest_event('GET', '/message/abc123')
        assert event['routeKey'] == 'GET /message/abc123'
        assert event['requestContext']['http']['method'] == 'GET'
        assert event['requestContext']['http']['path'] == '/message/abc123'
    
    def test_creates_post_event_with_body(self):
        """Test creating a POST event with a body."""
        body = {'message': 'Hello, world!'}
        event = create_rest_event('POST', '/message', body=body)
        assert event['routeKey'] == 'POST /message'
        assert 'body' in event
        assert '"message"' in event['body']
    
    def test_adds_leading_slash(self):
        """Test that path gets a leading slash if missing."""
        event = create_rest_event('GET', 'message')
        assert event['rawPath'] == '/message'
