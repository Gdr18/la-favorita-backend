from flask import Blueprint, request, url_for, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from pymongo import errors, ReturnDocument

from ..services.auth_service import generate_token, revoke_token, google
from ..utils.db_utils import db, bcrypt
from ..utils.exceptions_management import handle_unexpected_error, ClientCustomError, handle_duplicate_key_error

auth_route = Blueprint("auth", __name__)


@auth_route.route("/auth/login", methods=["POST"])
def login():
    try:
        user_data = request.get_json()
        user_request = db.users.find_one({"email": user_data.get("email")})
        if user_request:
            if bcrypt.check_password_hash(user_request.get("password"), user_data.get("password")):
                token = generate_token(user_request)
                return (
                    jsonify(
                        msg=f"El usuario '{user_request.get('_id')}' ha iniciado sesión de forma manual", token=token
                    ),
                    200,
                )
            raise ClientCustomError("password")
        raise ClientCustomError("email", "not_found")
    except ClientCustomError as e:
        if e.function == "not_found":
            return e.json_response_not_found()
        if e.resource == "password":
            return e.json_response_not_match()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        token_jti = get_jwt().get("jti")
        token_exp = get_jwt().get("exp")
        revoked_user = revoke_token(token_jti, token_exp)
        return revoked_user
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/auth/login/google")
def login_google():
    try:
        redirect_uri = url_for("auth.authorize_google", _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/auth/google")
def authorize_google():
    try:
        token = google.authorize_access_token()
        # userinfo_endpoint = google.server_metadata["userinfo_endpoint"]
        # response = google.get(userinfo_endpoint)
        # user_info = response.json()
        nonce = request.args.get("nonce")
        user_info = google.parse_id_token(token, nonce=nonce)

        user_data = {"name": user_info.get("name"), "auth_provider": "google", "confirmed": True}

        user = db.users.find_one_and_update(
            {"email": user_info.get("email")}, {"$set": user_data}, upsert=True, return_document=ReturnDocument.AFTER
        )
        if user:
            jwt_token = generate_token(user)
            return (
                jsonify(
                    {"msg": f"""El usuario '{user.get("_id")}' ha iniciado sesión con Google""", "token": jwt_token}
                ),
                200,
            )
        raise Exception("Error al escribir en la base de datos")
    except Exception as e:
        return handle_unexpected_error(e)
