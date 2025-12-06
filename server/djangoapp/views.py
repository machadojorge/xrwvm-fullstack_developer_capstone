"""
Views for the djangoapp application, including authentication,
dealerships, reviews, and car models.
"""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User

from .models import CarMake, CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    """
    Login user method. Authenticates user with username and password
    sent in JSON body and returns a JSON response with authentication status.
    """
    data = json.loads(request.body)
    username = data.get('userName')
    password = data.get('password')

    user = authenticate(username=username, password=password)
    response_data = {"userName": username}

    if user is not None:
        login(request, user)
        response_data["status"] = "Authenticated"

    return JsonResponse(response_data)


@csrf_exempt
def logout_request(request):
    """
    Logout the current authenticated user and return empty username.
    """
    if request.user.is_authenticated:
        logout(request)
    return JsonResponse({"userName": ""})


def registration(request):
    """
    Register a new user from JSON request body.
    Returns JSON with username and authentication status or error.
    """
    data = json.loads(request.body)
    username = data.get('userName')
    password = data.get('password')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')

    username_exist = False

    try:
        User.objects.get(username=username)
        username_exist = True
    except User.DoesNotExist:
        logger.debug(f"{username} is new user")

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})

    return JsonResponse({"userName": username, "error": "Already Registered"})


def get_cars(request):
    """
    Return a JSON response with all car models and their makes.
    If the database is empty, it initializes it first.
    """
    count = CarMake.objects.filter().count()
    if count == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = [
        {"CarModel": car_model.name, "CarMake": car_model.car_make.name}
        for car_model in car_models
    ]
    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state="All"):
    """
    Return a JSON response with all dealerships.
    If a state is provided, filters by state.
    """
    endpoint = "/fetchDealers" if state == "All" else f"/fetchDealers/{state}"
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_details(request, dealer_id):
    """
    Return a JSON response with details of a specific dealer.
    """
    if dealer_id:
        endpoint = f"/fetchReviews/dealer/{dealer_id}"
        dealer_data = get_request(endpoint)
        dealer_info = dealer_data[0] if isinstance(dealer_data, list) and dealer_data else {}
        return JsonResponse({"status": 200, "dealer": [dealer_info]})
    return JsonResponse({"status": 400, "message": "Bad Request"})


def get_dealer_reviews(request, dealer_id):
    """
    Return a JSON response with all reviews for a specific dealer.
    Each review is augmented with a sentiment.
    """
    if dealer_id:
        endpoint = f"/fetchReviews/dealer/{dealer_id}"
        reviews = get_request(endpoint)
        for review_detail in reviews:
            sentiment = analyze_review_sentiments(review_detail.get('review', ''))
            review_detail['sentiment'] = sentiment.get('sentiment', 'neutral')
        return JsonResponse({"status": 200, "reviews": reviews})
    return JsonResponse({"status": 400, "message": "Bad Request"})


def add_review(request):
    """
    Add a review to a dealer.
    Expects JSON body with review data.
    Returns JSON with status code.
    """
    if not request.user.is_anonymous:
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status": 200})
        except Exception as err:
            logger.error(f"Error posting review: {err}")
            return JsonResponse({"status": 401, "message": "Error in posting review"})
    return JsonResponse({"status": 403, "message": "Unauthorized"})
