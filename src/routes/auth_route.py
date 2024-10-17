from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..utils.exceptions_management import handle_unexpected_error, ClientCustomError
from ..services.auth_service import login_user

auth_route = Blueprint("auth", __name__)


@auth_route.route("/login", methods=["POST"])
def login():
    try:
        user_data = request.get_json()
        authenticated_user = login_user(user_data)
        return authenticated_user
    except ClientCustomError as e:
        if e.resource == "email":
            return e.json_response_not_found()
        if e.resource == "password":
            return e.json_response_not_match()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    pass
