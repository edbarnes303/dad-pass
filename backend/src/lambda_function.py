from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.exceptions import InternalServerError
from aws_lambda_powertools.utilities.typing import LambdaContext
import logging
import random
import boto3
from botocore.exceptions import ClientError
import os
import time
from decimal import Decimal

log: Logger = Logger()
Logger("botocore").setLevel(logging.INFO)
Logger("urllib3").setLevel(logging.INFO)

app = APIGatewayHttpResolver()

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['MESSAGES_TABLE_NAME'])

# TTL duration options in seconds
TTL_OPTIONS = {
    '15min': 900,
    '1hour': 3600,
    '1day': 86400,
    '5days': 432000
}

# Handler
@log.inject_lambda_context()
def handler(event: dict, context: LambdaContext) -> dict:
    print(event)
    return app.resolve(event, context)


# Now expects /message/<message_key> as path param
@app.get("/dad-pass/<message_key>")
def get_message(message_key) -> dict:
    try:
        response = table.get_item(Key={'messageKey': message_key})
        
        if 'Item' not in response:
            return {'message': 'Message is no longer available'}
        
        item = response['Item']
        current_time = int(time.time())
        
        # Check if message has expired
        ttl = item.get('ttl', 0)
        ttl_value = int(ttl) if isinstance(ttl, (int, Decimal)) else 0
        
        if ttl_value < current_time:
            # Delete expired message
            table.delete_item(Key={'messageKey': message_key})
            return {'message': 'Message is no longer available'}
        
        # Delete message after retrieval (one-time access)
        table.delete_item(Key={'messageKey': message_key})
        
        # Return the message data (excluding internal fields)
        message_data = {k: v for k, v in item.items() if k not in ['messageKey', 'ttl']}
        return message_data
        
    except Exception as e:
        log.error(f"Error retrieving message: {str(e)}")
        return {'message': 'Message is no longer available'}


@app.post("/dad-pass")
def create_message() -> dict:
    try:
        # Generate a random message key
        message_key = generate_random_id(10)  # Longer for better uniqueness
        message_in = app.current_event.json_body
        
        # Get TTL option from request, default to 5 days
        ttl_option = message_in.pop('ttlOption', '5days')
        ttl_duration = TTL_OPTIONS.get(ttl_option, TTL_OPTIONS['5days'])
        ttl_timestamp = int(time.time()) + ttl_duration
        
        # Prepare item for DynamoDB
        item = {
            'messageKey': message_key,
            'ttl': ttl_timestamp,
            **message_in
        }
        
        # Store in DynamoDB with condition to prevent overwriting existing key
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(messageKey)'
        )
        
        return {'messageKey': message_key}
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            log.error(f"Key collision detected for message key: {message_key}")
            raise InternalServerError("Key collision occurred, this is rare. Please try again.")
        log.error(f"Error creating message: {str(e)}")
        raise InternalServerError("Failed to create message")
        
    except Exception as e:
        log.error(f"Error creating message: {str(e)}")
        raise InternalServerError("Failed to create message")


def generate_random_id(length: int) -> str:
    return ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=length))
