from datetime import datetime, date
import json
import re
from aws_lambda_powertools import Logger
from typing import Any, Dict, Tuple, Callable, Optional
import boto3
import base64
from cryptography.fernet import Fernet

log = Logger()

#
# Encryption utilities
#

def _load_master_key_from_ssm() -> bytes:
    """
    Retrieves the master encryption key from AWS SSM Parameter Store.
    This is called once at module import time (Lambda container initialization).
    
    Returns:
        The master key as bytes, suitable for Fernet encryption
    """
    ssm = boto3.client('ssm')
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

# Load the master key once at module import time (Lambda cold start only)
_MASTER_KEY = _load_master_key_from_ssm()

def encrypt_message(plaintext: str) -> str:
    """
    Encrypts a plaintext message using Fernet symmetric encryption.
    
    Args:
        plaintext: The message text to encrypt
    
    Returns:
        Base64-encoded encrypted message (URL-safe)
    """
    try:
        fernet = Fernet(_MASTER_KEY)
        encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')  # Fernet already returns base64-encoded
    except Exception as e:
        log.error(f"Encryption failed: {str(e)}")
        raise

def decrypt_message(ciphertext: str) -> str:
    """
    Decrypts an encrypted message using Fernet symmetric encryption.
    
    Args:
        ciphertext: Base64-encoded encrypted message
    
    Returns:
        Decrypted plaintext message
    """
    try:
        fernet = Fernet(_MASTER_KEY)
        decrypted_bytes = fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        log.error(f"Decryption failed: {str(e)}")
        raise

#
# Utility functions
#


def create_rest_event(method: str, path: str, body: Optional[dict] = None) -> dict:
    """
    Creates a REST API Gateway event payload similar to those in run_local.py

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        path: API path (e.g., '/students', '/students/123')
        body: Optional request body as a dictionary

    Returns:
        A dictionary representing an API Gateway event payload
    """
    # Ensure path starts with a forward slash
    if not path.startswith('/'):
        path = '/' + path

    # Build routeKey with the method and path
    route_key = f"{method} {path}"

    # Create the basic event structure
    event = {
        "version": "2.0",
        "routeKey": route_key,
        "rawPath": path,
        "headers": {
            "accept": "application/json"
        },
        "requestContext": {
            "http": {
                "method": method,
                "path": path
            },
            "stage": "$default"
        },
        "isBase64Encoded": False
    }

    # Add body if provided
    if body:
        # Escape JSON string for embedding in another JSON string
        event["body"] = json.dumps(body)

    return event

