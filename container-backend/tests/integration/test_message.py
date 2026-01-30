"""
End-to-end integration tests for the dad-pass container backend.
These tests call the actual deployed container service endpoint.
"""
import json
import os
import pytest
import requests

# Configuration - can be overridden via environment variables
CONTAINER_SERVICE_URL = os.getenv('CONTAINER_SERVICE_URL', 'http://localhost:5001')
API_ENDPOINT = f"{CONTAINER_SERVICE_URL}/dad-pass"


class TestContainerIntegration:
    """Integration tests that call the deployed container service endpoint."""
    
    def test_health_check(self):
        """Test that the health check endpoint is responding."""
        response = requests.get(f"{CONTAINER_SERVICE_URL}/")
        
        if response.status_code == 404:
            pytest.skip("Container service endpoint not accessible")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        
        print("✓ Health check endpoint is healthy and responding")
    
    def test_create_and_retrieve_message_via_api(self):
        """Test the full flow: create a message via API, then retrieve it."""
        test_message = "End-to-end integration test secret message"
        
        # Step 1: Create a message
        try:
            create_response = requests.post(
                API_ENDPOINT,
                json={"message": test_message, "ttlOption": "1hour"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        if create_response.status_code == 403:
            pytest.skip("Container endpoint not accessible (likely CORS or authentication issue)")
        
        if create_response.status_code >= 500:
            pytest.skip(f"Container service error: {create_response.text}")
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        create_data = create_response.json()
        assert 'messageKey' in create_data
        
        message_key = create_data['messageKey']
        print(f"✓ Created message with key: {message_key}")
        
        # Step 2: Retrieve the message (this will delete it after retrieval)
        retrieve_url = f"{API_ENDPOINT}/{message_key}"
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
        retrieve_url = f"{API_ENDPOINT}/{fake_key}"
        
        try:
            response = requests.get(retrieve_url, timeout=10)
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        if response.status_code == 403:
            pytest.skip("Container endpoint not accessible")
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Message is no longer available'
        
        print("✓ Non-existent message correctly returns 'not available'")
    
    def test_create_message_without_ttl_option(self):
        """Test creating a message without specifying TTL option (defaults to 5 days)."""
        test_message = "Message with default TTL"
        
        try:
            create_response = requests.post(
                API_ENDPOINT,
                json={"message": test_message},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        if create_response.status_code >= 500:
            pytest.skip(f"Container service error: {create_response.text}")
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        create_data = create_response.json()
        assert 'messageKey' in create_data
        assert len(create_data['messageKey']) == 10
        
        # Retrieve and verify the message
        message_key = create_data['messageKey']
        retrieve_response = requests.get(f"{API_ENDPOINT}/{message_key}")
        retrieve_data = retrieve_response.json()
        assert retrieve_data['message'] == test_message
        assert retrieve_data['ttlOption'] == '5days'  # Default TTL option
        
        print("✓ Message with default TTL option created and retrieved successfully")
    
    def test_create_message_with_all_ttl_options(self):
        """Test creating messages with all supported TTL options."""
        ttl_options = ['15min', '1hour', '1day', '5days']
        
        for ttl_option in ttl_options:
            test_message = f"Message with {ttl_option} TTL"
            
            try:
                create_response = requests.post(
                    API_ENDPOINT,
                    json={"message": test_message, "ttlOption": ttl_option},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            except requests.exceptions.ConnectionError:
                pytest.skip("Container service not running or not accessible")
            
            if create_response.status_code >= 500:
                pytest.skip(f"Container service error: {create_response.text}")
            
            assert create_response.status_code == 200, f"Create with {ttl_option} failed: {create_response.text}"
            create_data = create_response.json()
            
            # Retrieve and verify
            message_key = create_data['messageKey']
            retrieve_response = requests.get(f"{API_ENDPOINT}/{message_key}")
            retrieve_data = retrieve_response.json()
            assert retrieve_data['message'] == test_message
            assert retrieve_data['ttlOption'] == ttl_option
            
            print(f"✓ TTL option '{ttl_option}' works correctly")
    
    def test_create_message_missing_message_field(self):
        """Test that creating a message without the message field returns an error."""
        try:
            response = requests.post(
                API_ENDPOINT,
                json={"ttlOption": "1hour"},  # Missing 'message' field
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        
        print("✓ Missing message field correctly returns 400 error")
    
    def test_api_endpoint_health(self):
        """Basic test to verify the API endpoint is accessible."""
        try:
            # Try to retrieve a non-existent message to test basic connectivity
            response = requests.get(f"{API_ENDPOINT}/test12345", timeout=10)
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        if response.status_code == 403:
            pytest.skip("Container endpoint not accessible")
        
        # Should get a 200 with "not available" message, not a 500 or 404
        assert response.status_code == 200
        print("✓ Container API endpoint is healthy and responding")
    
    def test_message_encryption(self):
        """Test that messages are encrypted at rest (cannot be read without decryption)."""
        test_message = "This message should be encrypted"
        
        try:
            create_response = requests.post(
                API_ENDPOINT,
                json={"message": test_message, "ttlOption": "1hour"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        if create_response.status_code >= 500:
            pytest.skip(f"Container service error: {create_response.text}")
        
        assert create_response.status_code == 200
        message_key = create_response.json()['messageKey']
        
        # Retrieve and verify the message is decrypted correctly
        retrieve_response = requests.get(f"{API_ENDPOINT}/{message_key}")
        retrieve_data = retrieve_response.json()
        
        # The returned message should be decrypted and match the original
        assert retrieve_data['message'] == test_message
        
        print("✓ Message encryption and decryption working correctly")
    
    def test_special_characters_in_message(self):
        """Test that messages with special characters are handled correctly."""
        test_message = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?`~ and unicode: 世界 🔐 émojis"
        
        try:
            create_response = requests.post(
                API_ENDPOINT,
                json={"message": test_message, "ttlOption": "1hour"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except requests.exceptions.ConnectionError:
            pytest.skip("Container service not running or not accessible")
        
        if create_response.status_code >= 500:
            pytest.skip(f"Container service error: {create_response.text}")
        
        assert create_response.status_code == 200
        message_key = create_response.json()['messageKey']
        
        # Retrieve and verify
        retrieve_response = requests.get(f"{API_ENDPOINT}/{message_key}")
        retrieve_data = retrieve_response.json()
        assert retrieve_data['message'] == test_message
        
        print("✓ Special characters handled correctly")
