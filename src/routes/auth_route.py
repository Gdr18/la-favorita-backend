from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..utils.exceptions_management import handle_unexpected_error, ResourceNotFoundError
from ..services.auth_service import AuthService

auth_route = Blueprint("auth", __name__)


@auth_route.route("/login", methods=["POST"])
def login_user():
    try:
        data = request.get_json()
        authenticated_user = AuthService(data.get("email"), data.get("password")).login_user()
        return authenticated_user
    except ResourceNotFoundError as e:
        return e.json_response()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    pass
