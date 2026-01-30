# This file creates a simple sandbox for iterating on and debugging lambda functions locally

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from aws_lambda_powertools.utilities.typing import LambdaContext
import utils

events = {
    "CREATE_MESSAGE": utils.create_rest_event("POST", "/dad-pass", body={"message": "Hello, world!"}),
    "GET_MESSAGE": utils.create_rest_event("GET", "/dad-pass/test"),
}


class MockContext(LambdaContext):
    def __init__(self,
                 invoked_function_arn="arn:aws:lambda:us-west-2:0000000000:function:mock_function-name:dev",
                 function_name="mock_function_name",
                 memory_limit_in_mb=64,
                 aws_request_id="mock_id"):
        print("Mock context initialized")


def run(event_key, handler_function):
    # Initialize a context to pass into the handler method
    context = MockContext

    # Get the event dictionary from events
    event = events[event_key]

    # For backwards compatibility, handle string events
    if isinstance(event, str):
        event = json.loads(event)

    # Print event in a readable format
    print("\nEVENT:")
    print(json.dumps(event, indent=4))

    result = handler_function(event, context)

    # Log the result of the main handler as json
    print("\nRESULT:")
    print("\n" + json.dumps(result, indent=4, sort_keys=True, default=str))
    print("\n\nBODY:")
    body = json.loads(result["body"])
    print("\n" + json.dumps(body, indent=4, sort_keys=True, default=str))
    return result


if __name__ == '__main__':
    sys.path.append(os.getcwd())
    from src import lambda_function

    event_name = sys.argv[1]
    print("Running event: " + event_name)
    run(event_name, lambda_function.handler)
