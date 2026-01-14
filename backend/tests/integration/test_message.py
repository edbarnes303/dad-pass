import json
import sys
import os
import pytest
from pathlib import Path
import lambda_function
import utils

from aws_lambda_powertools.utilities.typing import LambdaContext

# Get the service module's base directory
service_dir = Path(__file__).parent.parent.parent
# Add the source directory to the Python path
src_dir = service_dir / "src"
sys.path.insert(0, str(src_dir))

# Add the service root directory to import run_local.py contents if needed
sys.path.insert(0, str(service_dir))

class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-easst-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")

mock_context = MockContext

def test_create_message_integration():
    """
    Integration test that replicates what happens when run_local.py is ran with CREATE_MESSAGE_REST.
    """

    create_message_event = utils.create_rest_event("POST", "/message", body={"message": "Hello, world!"})

    # Call the lambda handler with the event and context
    result = lambda_function.handler(create_message_event, mock_context)

    # Verify that the response is successful
    assert result["statusCode"] == 200

    # Parse the response body
    body = json.loads(result["body"])

    # Verify that we got a message key
    assert isinstance(body, dict)
    assert "messageKey" in body
    assert isinstance(body["messageKey"], str)
    assert len(body["messageKey"]) == 5


