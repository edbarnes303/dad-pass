from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
import logging
import random

log: Logger = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

app = APIGatewayHttpResolver()

message_store: dict[str, str] = {"test": "This is a sample message"}

# Handler
@log.inject_lambda_context()
def handler(event: dict, context: LambdaContext) -> dict:
    print(event)
    return app.resolve(event, context)


# Now expects /message/<message_key> as path param
@app.get("/dad-pass/<message_key>")
def get_message(message_key) -> dict:
    message = message_store.get(message_key, "Message is no longer available")
    # Remove message from store after retrieving it
    message_store.pop(message_key, None)
    return { 'message': message }


@app.post("/dad-pass")
def create_message() -> dict:
    # Generate a random 5 character message ID
    message_key = generate_random_id(5)
    message_in = app.current_event.json_body
    message_in['messageKey'] = message_key
    message_store[message_key] = message_in
    return {'messageKey': message_key}


def generate_random_id(length: int) -> str:
    return ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))
