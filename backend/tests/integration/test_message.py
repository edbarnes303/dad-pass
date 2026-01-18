"""
End-to-end integration tests for the dad-pass backend.
These tests call the actual deployed Lambda function and API Gateway endpoint.
"""
import json
import os
import pytest
import boto3
import requests
from botocore.exceptions import ClientError

# Configuration
LAMBDA_FUNCTION_NAME = os.getenv('LAMBDA_FUNCTION_NAME', 'dad-pass-service-prod')
API_GATEWAY_URL = 'https://twyukas531.execute-api.us-east-2.amazonaws.com/dad-pass'
REGION = 'us-east-2'


class TestLambdaIntegration:
    """Integration tests that invoke the deployed Lambda function directly."""
    
    @pytest.fixture(scope='class')
    def lambda_client(self):
        """Create a Lambda client for invoking functions."""
        return boto3.client('lambda', region_name=REGION)
    
    def test_create_message_via_lambda(self, lambda_client):
        """Test creating a message by invoking the Lambda function directly."""
        # Create the event payload for creating a message
        event = {
            "version": "2.0",
            "routeKey": "POST /dad-pass",
            "rawPath": "/dad-pass",
            "headers": {
                "accept": "application/json"
            },
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/dad-pass"
                },
                "stage": "$default"
            },
            "isBase64Encoded": False,
            "body": json.dumps({"message": "Test secret from Lambda invoke", "ttlOption": "1day"})
        }
        
        try:
            # Invoke the Lambda function
            response = lambda_client.invoke(
                FunctionName=LAMBDA_FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            # Parse the response
            payload = json.loads(response['Payload'].read())
            assert response['StatusCode'] == 200
            assert 'body' in payload
            
            body = json.loads(payload['body'])
            assert 'messageKey' in body
            assert isinstance(body['messageKey'], str)
            assert len(body['messageKey']) == 10
            
            print(f"✓ Lambda invoke test passed. Message key: {body['messageKey']}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ResourceNotFoundException':
                pytest.skip(f"Lambda function '{LAMBDA_FUNCTION_NAME}' not found")
            else:
                pytest.skip(f"Lambda function not accessible: {e}")
        except Exception as e:
            # Handle NoCredentialsError and other boto3 errors
            if 'credential' in str(e).lower() or 'NoCredentialsError' in str(type(e).__name__):
                pytest.skip("AWS credentials not configured for Lambda invoke test")
            raise


class TestAPIGatewayIntegration:
    """Integration tests that call the deployed API Gateway endpoint."""
    
    def test_create_and_retrieve_message_via_api(self):
        """Test the full flow: create a message via API, then retrieve it."""
        test_message = "End-to-end integration test secret message"
        
        # Step 1: Create a message
        create_response = requests.post(
            API_GATEWAY_URL,
            json={"message": test_message, "ttlOption": "1hour"},
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code == 403:
            pytest.skip("API Gateway endpoint not accessible (likely CORS or authentication issue)")
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        create_data = create_response.json()
        assert 'messageKey' in create_data
        
        message_key = create_data['messageKey']
        print(f"✓ Created message with key: {message_key}")
        
        # Step 2: Retrieve the message (this will delete it after retrieval)
        retrieve_url = f"{API_GATEWAY_URL}/{message_key}"
        retrieve_response = requests.get(retrieve_url)
        
        assert retrieve_response.status_code == 200, f"Retrieve failed: {retrieve_response.text}"
        retrieve_data = retrieve_response.json()
        assert 'message' in retrieve_data
        assert retrieve_data['message'] == test_message
        
        print(f"✓ Retrieved and verified message: {retrieve_data['message'][:30]}...")
        
        # Step 3: Verify the message is deleted (second retrieval should fail)
        second_retrieve = requests.get(retrieve_url)
        assert second_retrieve.status_code == 200
        second_data = second_retrieve.json()
        assert second_data['message'] == 'Message is no longer available'
        
        print("✓ Verified message was deleted after first retrieval")
    
    def test_retrieve_nonexistent_message(self):
        """Test retrieving a message that doesn't exist."""
        fake_key = "xxxxx12345"
        retrieve_url = f"{API_GATEWAY_URL}/{fake_key}"
        
        response = requests.get(retrieve_url)
        
        if response.status_code == 403:
            pytest.skip("API Gateway endpoint not accessible")
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Message is no longer available'
        
        print("✓ Non-existent message correctly returns 'not available'")
    
    
    def test_api_endpoint_health(self):
        """Basic test to verify the API endpoint is accessible."""
        # Try to retrieve a non-existent message to test basic connectivity
        response = requests.get(f"{API_GATEWAY_URL}/test12345")
        
        if response.status_code == 403:
            pytest.skip("API Gateway endpoint not accessible")
        
        # Should get a 200 with "not available" message, not a 500 or 404
        assert response.status_code == 200
        print("✓ API Gateway endpoint is healthy and responding")


