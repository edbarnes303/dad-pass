from datetime import datetime, date
import json
import re
from aws_lambda_powertools import Logger
from typing import Any, Dict, Tuple, Callable, Optional

log = Logger()

#
# Utility functions
#

def to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel(name):
    components = name.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


def camelfy(dict_or_list):
    if dict_or_list == None:
        return None
    if isinstance(dict_or_list, dict):
        return camelfy_object(dict_or_list)
    elif isinstance(dict_or_list, list):
        new_list = []
        for item in dict_or_list:
            new_list.append(camelfy_object(item))

        return new_list
    else:
        raise Exception("camelfy could not parse type " + str(type(dict_or_list)))


def camelfy_object(object: dict) -> dict:
    new_object_dict = {}
    for key in object.keys():
        if isinstance(object[key], datetime) or isinstance(object[key], date):
            new_object_dict[to_camel(key)] = str(object[key])
        else:
            new_object_dict[to_camel(key)] = object[key]
    return new_object_dict


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

