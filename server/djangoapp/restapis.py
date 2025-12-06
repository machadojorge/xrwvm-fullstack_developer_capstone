"""
REST API utility functions to interact with backend and sentiment analyzer.
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

backend_url = os.getenv('backend_url', default="http://localhost:3030")
sentiment_analyzer_url = os.getenv('sentiment_analyzer_url', default="http://localhost:5050/")


def get_request(endpoint, **kwargs):
    """Make a GET request to the backend with optional query parameters."""
    params = ""
    if kwargs:
        for key, value in kwargs.items():
            params += f"{key}={value}&"

    request_url = backend_url + endpoint + "?" + params
    print(f"GET from {request_url}")

    try:
        response = requests.get(request_url, timeout=5)
        return response.json()
    except requests.exceptions.RequestException:
        print("Network exception occurred")
        return {}


def analyze_review_sentiments(text):
    """Call the sentiment analyzer API and return the sentiment result."""
    request_url = sentiment_analyzer_url + "analyze/" + text
    try:
        response = requests.get(request_url, timeout=5)
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        print("Network exception occurred")
        return {"sentiment": "neutral"}


def post_review(data_dict):
    """POST a review to the backend and return the response."""
    request_url = backend_url + "/insert_review"
    try:
        response = requests.post(request_url, json=data_dict, timeout=5)
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException:
        print("Network exception occurred")
        return {"status": 500, "message": "Network error"}

