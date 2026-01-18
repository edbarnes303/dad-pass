import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
import os

# Set required environment variable
os.environ['MESSAGES_TABLE_NAME'] = 'test-messages-table'

# Mock boto3 before importing lambda_function to prevent SSM and DynamoDB calls during import
mock_key = Fernet.generate_key()
with patch('boto3.client') as mock_client, patch('boto3.resource') as mock_resource:
    # Mock SSM client
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {
        'Parameter': {'Value': mock_key.decode('utf-8')}
    }
    mock_client.return_value = mock_ssm
    
    # Mock DynamoDB resource
    mock_dynamodb = MagicMock()
    mock_resource.return_value = mock_dynamodb
    
    # Get the service module's base directory
    service_dir = Path(__file__).parent.parent.parent
    # Add the source directory to the Python path
    src_dir = service_dir / "src"
    sys.path.insert(0, str(src_dir))
    
    from lambda_function import generate_random_id


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
