"""
Unit tests for the dad-pass container backend Flask app.
These tests mock AWS services and test the application logic.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
import os
import json
import time

# Set required environment variables before importing app
os.environ['MESSAGES_TABLE_NAME'] = 'test-messages-table'
os.environ['AWS_REGION'] = 'us-east-1'

# Generate a mock encryption key for tests
mock_key = Fernet.generate_key()

# Mock boto3 before importing app to prevent SSM and DynamoDB calls during import
with patch('boto3.client') as mock_client, patch('boto3.resource') as mock_resource:
    # Mock SSM client
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': mock_key.decode('utf-8')}
    }
    mock_client.return_value = mock_ssm
    
    # Mock DynamoDB resource
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_resource.return_value = mock_dynamodb
    
    # Get the service module's base directory
    service_dir = Path(__file__).parent.parent.parent
    # Add the source directory to the Python path
    src_dir = service_dir / "app"
    sys.path.insert(0, str(src_dir))
    
    from app import generate_random_id, app, encrypt_message, decrypt_message


class TestGenerateRandomId:
    """Unit tests for the generate_random_id function."""
    
    def test_returns_correct_length(self):
        """Test that the function returns an ID of the requested length."""
        for length in [1, 5, 10, 20]:
            result = generate_random_id(length)
            assert len(result) == length
    
    def test_contains_only_alphanumeric_characters(self):
        """Test that the generated ID contains only alphanumeric characters."""
        result = generate_random_id(100)
        assert result.isalnum()
    
    def test_generates_different_ids(self):
        """Test that consecutive calls generate different IDs."""
        ids = [generate_random_id(10) for _ in range(10)]
        assert len(ids) == len(set(ids))


class TestEncryption:
    """Unit tests for encryption/decryption functions."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypting and decrypting returns the original message."""
        original_message = "This is a secret message!"
        encrypted = encrypt_message(original_message)
        decrypted = decrypt_message(encrypted)
        assert decrypted == original_message
    
    def test_encrypted_message_is_different(self):
        """Test that the encrypted message is different from the original."""
        original_message = "This is a secret message!"
        encrypted = encrypt_message(original_message)
        assert encrypted != original_message
    
    def test_encrypt_empty_string(self):
        """Test that encrypting an empty string works."""
        encrypted = encrypt_message("")
        decrypted = decrypt_message(encrypted)
        assert decrypted == ""
    
    def test_encrypt_unicode_message(self):
        """Test that encrypting Unicode characters works."""
        original_message = "Hello 世界! 🔐"
        encrypted = encrypt_message(original_message)
        decrypted = decrypt_message(encrypted)
        assert decrypted == original_message


class TestFlaskRoutes:
    """Unit tests for Flask route handlers."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_check(self, client):
        """Test the health check endpoint returns healthy status."""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    @patch('app.table')
    def test_create_message_success(self, mock_table, client):
        """Test creating a message successfully."""
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test secret message', 'ttlOption': '1hour'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'messageKey' in data
        assert len(data['messageKey']) == 10
        assert data['messageKey'].isalnum()
    
    @patch('app.table')
    def test_create_message_without_ttl_option(self, mock_table, client):
        """Test creating a message with default TTL option."""
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test secret message'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'messageKey' in data
    
    def test_create_message_missing_message(self, client):
        """Test creating a message without the required message field."""
        response = client.post(
            '/dad-pass',
            data=json.dumps({'ttlOption': '1hour'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.table')
    def test_get_message_success(self, mock_table, client):
        """Test retrieving a message successfully."""
        # Create an encrypted message
        test_message = "Secret message"
        encrypted = encrypt_message(test_message)
        future_ttl = int(time.time()) + 3600  # 1 hour from now
        
        mock_table.get_item.return_value = {
            'Item': {
                'messageKey': 'abc123xyz0',
                'encryptedMessage': encrypted,
                'ttl': future_ttl,
                'ttlOption': '1hour'
            }
        }
        mock_table.delete_item.return_value = {}
        
        response = client.get('/dad-pass/abc123xyz0')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == test_message
        assert data['ttlOption'] == '1hour'
        
        # Verify delete was called (one-time access)
        mock_table.delete_item.assert_called_once_with(Key={'messageKey': 'abc123xyz0'})
    
    @patch('app.table')
    def test_get_message_not_found(self, mock_table, client):
        """Test retrieving a non-existent message."""
        mock_table.get_item.return_value = {}  # No 'Item' key
        
        response = client.get('/dad-pass/nonexistent1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Message is no longer available'
    
    @patch('app.table')
    def test_get_message_expired(self, mock_table, client):
        """Test retrieving an expired message."""
        # Create an encrypted message with expired TTL
        test_message = "Expired secret"
        encrypted = encrypt_message(test_message)
        expired_ttl = int(time.time()) - 3600  # 1 hour ago (expired)
        
        mock_table.get_item.return_value = {
            'Item': {
                'messageKey': 'expired123',
                'encryptedMessage': encrypted,
                'ttl': expired_ttl,
                'ttlOption': '1hour'
            }
        }
        mock_table.delete_item.return_value = {}
        
        response = client.get('/dad-pass/expired123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Message is no longer available'
        
        # Verify delete was called for cleanup
        mock_table.delete_item.assert_called_once_with(Key={'messageKey': 'expired123'})


class TestTTLOptions:
    """Unit tests for TTL option handling."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('app.table')
    @patch('app.time')
    def test_ttl_15min(self, mock_time, mock_table, client):
        """Test that 15min TTL is calculated correctly."""
        mock_time.time.return_value = 1000000
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test', 'ttlOption': '15min'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        # Verify put_item was called with correct TTL (current_time + 900)
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['ttl'] == 1000900  # 1000000 + 900
        assert item['ttlOption'] == '15min'
    
    @patch('app.table')
    @patch('app.time')
    def test_ttl_1hour(self, mock_time, mock_table, client):
        """Test that 1hour TTL is calculated correctly."""
        mock_time.time.return_value = 1000000
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test', 'ttlOption': '1hour'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['ttl'] == 1003600  # 1000000 + 3600
        assert item['ttlOption'] == '1hour'
    
    @patch('app.table')
    @patch('app.time')
    def test_ttl_1day(self, mock_time, mock_table, client):
        """Test that 1day TTL is calculated correctly."""
        mock_time.time.return_value = 1000000
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test', 'ttlOption': '1day'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['ttl'] == 1086400  # 1000000 + 86400
        assert item['ttlOption'] == '1day'
    
    @patch('app.table')
    @patch('app.time')
    def test_ttl_5days(self, mock_time, mock_table, client):
        """Test that 5days TTL is calculated correctly."""
        mock_time.time.return_value = 1000000
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test', 'ttlOption': '5days'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['ttl'] == 1432000  # 1000000 + 432000
        assert item['ttlOption'] == '5days'
    
    @patch('app.table')
    @patch('app.time')
    def test_ttl_invalid_defaults_to_5days(self, mock_time, mock_table, client):
        """Test that an invalid TTL option defaults to 5 days."""
        mock_time.time.return_value = 1000000
        mock_table.put_item.return_value = {}
        
        response = client.post(
            '/dad-pass',
            data=json.dumps({'message': 'Test', 'ttlOption': 'invalid'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['ttl'] == 1432000  # Defaults to 5days (432000)
