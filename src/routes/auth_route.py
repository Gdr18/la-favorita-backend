from flask import Blueprint, request, url_for
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
import requests

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
        if e.function == "not_found":
            return e.json_response_not_found()
        if e.resource == "password":
            return e.json_response_not_match()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        token_jti = get_jwt().get("jti")
        token_exp = get_jwt().get("exp")
        revoked_token = {"jti": token_jti, "exp": datetime.fromtimestamp(token_exp)}

        revoke_url = url_for("revoked_token.add_revoked_token", _external=True)
        response = requests.post(revoke_url, json=revoked_token)
        return response
    except Exception as e:
        return handle_unexpected_error(e)
