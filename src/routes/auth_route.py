from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime

from ..utils.db_utils import db
from ..utils.exceptions_management import handle_unexpected_error, ClientCustomError
from ..utils.successfully_responses import resource_added_msg
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
        new_revoked_token = db.revoked_tokens.insert_one(revoked_token)
        return resource_added_msg(new_revoked_token.inserted_id, "token revocado")
    except Exception as e:
        return handle_unexpected_error(e)
