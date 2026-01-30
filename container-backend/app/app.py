from flask import Flask, request, jsonify
import boto3
from botocore.exceptions import ClientError
import os
import time
import random
import logging
from decimal import Decimal
import base64
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

app = Flask(__name__)

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table_name = os.environ.get('MESSAGES_TABLE_NAME', 'dad-pass-messages-dev')
table = dynamodb.Table(table_name)

# TTL duration options in seconds
TTL_OPTIONS = {
    '15min': 900,
    '1hour': 3600,
    '1day': 86400,
    '5days': 432000
}

#
# Encryption utilities
#

def _load_master_key_from_ssm() -> bytes:
    """
    Retrieves the master encryption key from AWS SSM Parameter Store.
    
    Returns:
        The master key as bytes, suitable for Fernet encryption
    """
    ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    parameter_name = '/dad-pass/encryption-key'
    
    try:
        response = ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True  # Decrypt SecureString parameter
        )
        key_string = response['Parameter']['Value']
        log.info(f"Master encryption key loaded from SSM: {parameter_name}")
        return key_string.encode('utf-8')
    except Exception as e:
        log.error(f"Failed to retrieve encryption key from SSM: {str(e)}")
        raise


# Load the master key once at module initialization (when Flask app starts)
_MASTER_KEY = _load_master_key_from_ssm()


def _get_master_key() -> bytes:
    """Returns the cached master encryption key."""
    return _MASTER_KEY


def encrypt_message(plaintext: str) -> str:
    """
    Encrypts a plaintext message using Fernet symmetric encryption.
    
    Args:
        plaintext: The message text to encrypt
    
    Returns:
        Base64-encoded encrypted message (URL-safe)
    """
    try:
        fernet = Fernet(_get_master_key())
        encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')  # Fernet already returns base64-encoded
    except Exception as e:
        log.error(f"Encryption failed: {str(e)}")
        raise


def decrypt_message(ciphertext: str) -> str:
    """
    Decrypts an encrypted message using Fernet symmetric encryption.
    MASTER_KEY
    Args:
        ciphertext: Base64-encoded encrypted message
    
    Returns:
        Decrypted plaintext message
    """
    try:
        fernet = Fernet(_get_master_key())
        decrypted_bytes = fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        log.error(f"Decryption failed: {str(e)}")
        raise


def generate_random_id(length: int) -> str:
    """Generate a random alphanumeric ID."""
    return ''.join(random.choices(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", 
        k=length
    ))


#
# Routes
#

@app.route("/")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/dad-pass/<message_key>", methods=["GET"])
def get_message(message_key: str):
    """
    Retrieve and delete a message by its key (one-time access).
    """
    try:
        response = table.get_item(Key={'messageKey': message_key})
        
        if 'Item' not in response:
            return jsonify({'message': 'Message is no longer available'})
        
        item = response['Item']
        current_time = int(time.time())
        
        # Check if message has expired
        ttl = item.get('ttl', 0)
        ttl_value = int(ttl) if isinstance(ttl, (int, Decimal)) else 0
        
        if ttl_value < current_time:
            # Delete expired message
            table.delete_item(Key={'messageKey': message_key})
            return jsonify({'message': 'Message is no longer available'})
        
        # Delete message after retrieval (one-time access)
        table.delete_item(Key={'messageKey': message_key})
        
        # Decrypt the message
        encrypted_message = item.get('encryptedMessage', '')
        decrypted_message = decrypt_message(encrypted_message)
        
        # Return the decrypted message (maintaining API contract)
        return jsonify({
            'message': decrypted_message, 
            'ttlOption': item.get('ttlOption', '5days')
        })
        
    except Exception as e:
        log.error(f"Error retrieving message: {str(e)}")
        return jsonify({'message': 'Message is no longer available'})


@app.route("/dad-pass", methods=["POST"])
def create_message():
    """
    Create a new encrypted message with a unique key.
    """
    try:
        # Generate a random message key
        message_key = generate_random_id(10)  # Longer for better uniqueness
        message_in = request.get_json()
        
        if not message_in or 'message' not in message_in:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get TTL option from request, default to 5 days
        ttl_option = message_in.get('ttlOption', '5days')
        ttl_duration = TTL_OPTIONS.get(ttl_option, TTL_OPTIONS['5days'])
        ttl_timestamp = int(time.time()) + ttl_duration
        
        # Encrypt the message before storing
        encrypted_message = encrypt_message(message_in['message'])
        
        # Prepare item for DynamoDB (store encrypted message)
        item = {
            'messageKey': message_key,
            'ttl': ttl_timestamp,
            'encryptedMessage': encrypted_message,
            'ttlOption': ttl_option
        }
        
        # Store in DynamoDB with condition to prevent overwriting existing key
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(messageKey)'
        )
        
        return jsonify({'messageKey': message_key})
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            log.error(f"Key collision detected for message key: {message_key}")
            return jsonify({'error': 'Key collision occurred, this is rare. Please try again.'}), 500
        log.error(f"Error creating message: {str(e)}")
        return jsonify({'error': 'Failed to create message'}), 500
        
    except Exception as e:
        log.error(f"Error creating message: {str(e)}")
        return jsonify({'error': 'Failed to create message'}), 500


if __name__ == "__main__":
    # Run the Flask development server
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)