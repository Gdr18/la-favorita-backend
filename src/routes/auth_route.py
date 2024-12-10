from bson import ObjectId
from flask import Blueprint, request, url_for, jsonify
from flask_jwt_extended import jwt_required, get_jwt, decode_token
from pymongo import errors, ReturnDocument

from ..models.token_model import TokenModel
from ..models.user_model import UserModel
from ..services.auth_service import generate_access_token, generate_refresh_token, revoke_token, google
from ..services.email_service import send_email
from ..utils.db_utils import db, bcrypt
from ..utils.exceptions_management import handle_unexpected_error, ClientCustomError, handle_duplicate_key_error
from ..utils.successfully_responses import resource_msg

auth_route = Blueprint("auth", __name__)


@auth_route.route("/auth/login", methods=["POST"])
def login():
    try:
        user_data = request.get_json()
        user_requested = db.users.find_one({"email": user_data.get("email")})
        if user_requested:
            if bcrypt.check_password_hash(user_requested.get("password"), user_data.get("password")):
                if user_requested.get("confirmed"):
                    access_token = generate_access_token(user_requested)
                    refresh_token = generate_refresh_token(user_requested)
                    return (
                        jsonify(
                            msg=f"El usuario '{user_requested.get('_id')}' ha iniciado sesión de forma manual",
                            access_token=access_token,
                            refresh_token=refresh_token,
                        ),
                        200,
                    )
                raise ClientCustomError(user_requested.get("_id"), "not_confirmed")
            raise ClientCustomError("password")
        raise ClientCustomError("email", "not_found")
    except ClientCustomError as e:
        if e.function == "not_found":
            return e.json_response_not_found()
        if e.resource == "password":
            return e.json_response_not_match()
        if e.function == "not_confirmed":
            return e.json_response_not_confirmed()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        token = get_jwt()
        # TODO: Refactorizar cuando se cambie TokenModel
        revoked_token = revoke_token(token)
        refresh_token_deleted = TokenModel.delete_refresh_token_by_user_id(token.get("sub"))
        if revoked_token and refresh_token_deleted:
            return revoked_token
        raise Exception("Error al revocar el token")
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
        google_token = google.authorize_access_token()
        nonce = request.args.get("nonce")
        google_user_info = google.parse_id_token(google_token, nonce=nonce)

        user_data = {"name": google_user_info.get("name"), "auth_provider": "google", "confirmed": True}

        user = db.users.find_one_and_update(
            {"email": google_user_info.get("email")},
            {"$set": user_data},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if user:
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)
            return (
                jsonify(
                    {
                        "msg": f"""El usuario '{user.get("_id")}' ha iniciado sesión con Google""",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }
                ),
                200,
            )
        raise Exception("Error al escribir en la base de datos")
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/auth/refresh")
@jwt_required(refresh=True)
def refresh_users_token():
    try:
        user_id = get_jwt().get("sub")
        check_refresh_token = TokenModel.get_refresh_token_by_user_id(user_id)
        if check_refresh_token:
            user_data = db.users.find_one({"_id": ObjectId(user_id)})
            access_token = generate_access_token(user_data)
            return jsonify(access_token=access_token, msg="El token de acceso se ha generado"), 200
        raise ClientCustomError("refresh token", "not_found")
    except ClientCustomError as e:
        return e.json_response_not_found()
    except Exception as e:
        return handle_unexpected_error(e)


# TODO: Verificar si se puede comprobar que la entrada es a través de un email
@auth_route.route("/auth/confirm_email/<token>", methods=["GET"])
def confirm_email(token):
    try:
        user_identity = decode_token(token)
        user_id = user_identity.get("sub")
        user_requested = db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
        user_requested["confirmed"] = True
        user_object = UserModel(**user_requested)
        user_updated = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": user_object.to_dict()})
        if user_updated:
            return resource_msg(user_identity.get("sub"), "usuario", "confirmado")
        raise ClientCustomError("email", "not_found")
    except ClientCustomError as e:
        return e.json_response_not_found()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/auth/resend_email/<user_id>", methods=["POST"])
def resend_email(user_id):
    try:
        user_token = TokenModel.get_email_tokens_by_user_id(user_id)
        if len(user_token) < 5:
            user_data = db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                send_email(user_data)
                return resource_msg(user_id, "email de confirmación", "reenviado")
            raise ClientCustomError(f"usuario '{user_id}'", "not_found")
        raise ClientCustomError("email", "too_many_requests")
    except ClientCustomError as e:
        if e.function == "not_found":
            return e.json_response_not_found()
        if e.function == "too_many_requests":
            return e.json_response_too_many_requests()
    except Exception as e:
        return handle_unexpected_error(e)
