from flask import Blueprint, request, url_for, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt, decode_token
from pydantic import ValidationError
from pymongo.errors import PyMongoError
from sendgrid import SendGridException

from src.models.token_model import TokenModel
from src.models.user_model import UserModel
from src.services.email_service import send_email
from src.services.security_service import (
    generate_access_token,
    generate_refresh_token,
    revoke_access_token,
    delete_refresh_token,
    google,
    verify_password,
)
from src.utils.exception_handlers import (
    handle_unexpected_error,
    ValueCustomError,
    handle_validation_error,
    handle_send_email_error,
)
from src.utils.mongodb_exception_handlers import handle_mongodb_exception
from src.utils.json_responses import success_json_response

auth_route = Blueprint("auth", __name__)


@auth_route.route("/register", methods=["POST"])
def register() -> tuple[Response, int]:
    try:
        user_data = request.get_json()
        if user_data.get("role"):
            raise ValueCustomError("not_authorized_to_set", "role")
        else:
            user_object = UserModel(**user_data)
            new_user = user_object.insert_user()
            send_email({**user_object.model_dump(), "_id": new_user.inserted_id})
            return success_json_response(new_user.inserted_id, "usuario", "añadido", 201)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except SendGridException as e:
        return handle_send_email_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


# Se precisa de un login previo gestionado por el frontend
@auth_route.route("/change-email", methods=["POST"])
@jwt_required()
def change_email() -> tuple[Response, int]:
    try:
        user_data = request.get_json()
        user_id = get_jwt().get("sub")
        user_requested = UserModel.get_user_by_user_id_without_id(user_id)
        if user_requested.get("auth_provider") == "google":
            user_requested["auth_provider"] = "email"
            user_requested["confirmed"] = False
            if not user_data.get("password"):
                raise Exception("Se necesita contraseña para cambiar el email")
            user_requested["password"] = user_data.get("password")
        user_requested["email"] = user_data.get("email")
        user_object = UserModel(**user_requested)
        updated_user = user_object.update_user(user_id)
        send_email(updated_user)
        return success_json_response(user_id, "email del usuario", "cambiado")
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except SendGridException as e:
        return handle_send_email_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/login", methods=["POST"])
def login() -> tuple[Response, int]:
    try:
        user_data = request.get_json()
        user_requested = UserModel.get_user_by_email(user_data.get("email"))
        if not user_requested:
            raise ValueCustomError("not_found", "usuario")
        if not verify_password(user_requested.get("password"), user_data.get("password")):
            raise ValueCustomError("not_match")
        if not user_requested.get("confirmed"):
            raise ValueCustomError("not_confirmed")
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
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/logout", methods=["POST"])
@jwt_required()
def logout() -> tuple[Response, int]:
    try:
        token = get_jwt()
        revoke_access_token(token)
        delete_refresh_token(token["sub"])
        return success_json_response(token["sub"], "logout del usuario", "realizado")
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/login/google")
def login_google() -> tuple[Response, int]:
    try:
        redirect_uri = url_for("auth.authorize_google", _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/callback/google")
def authorize_google() -> tuple[Response, int]:
    try:
        google_token = google.authorize_access_token()
        nonce = request.args.get("nonce")
        google_user_info = google.parse_id_token(google_token, nonce=nonce)

        user_data = {
            "name": google_user_info.get("name"),
            "email": google_user_info.get("email"),
            "auth_provider": "google",
        }
        user_object = UserModel(**user_data)
        user = user_object.insert_or_update_user_by_email()
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
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/refresh-token")
@jwt_required(refresh=True)
def refresh_users_token() -> tuple[Response, int]:
    try:
        user_id = get_jwt().get("sub")
        check_refresh_token = TokenModel.get_refresh_token_by_user_id(user_id)
        if check_refresh_token:
            user_data = UserModel.get_user_by_user_id_without_id(user_id)
            access_token = generate_access_token(user_data)
            return jsonify(access_token=access_token, msg="El token de acceso se ha generado"), 200
        else:
            raise ValueCustomError("not_found", "refresh token")
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/confirm-email/<token>", methods=["GET"])
def confirm_email(token: str) -> tuple[Response, int]:
    try:
        user_identity = decode_token(token)
        user_id = user_identity.get("sub")
        user_requested = UserModel.get_user_by_user_id_without_id(user_id)
        if user_requested:
            user_requested["confirmed"] = True
            user_object = UserModel(**user_requested)
            user_object.update_user(user_id)
            return success_json_response(user_id, "usuario", "confirmado")
        else:
            raise ValueCustomError("not_found", "usuario")
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/resend-email/<user_id>", methods=["POST"])
def resend_email(user_id: str) -> tuple[Response, int]:
    try:
        user_token = TokenModel.get_email_tokens_by_user_id(user_id)
        if len(user_token) < 5:
            user_data = UserModel.get_user_by_user_id(user_id)
            if user_data:
                send_email(user_data)
                return success_json_response(user_id, "email de confirmación del usuario", "reenviado")
            else:
                raise ValueCustomError("not_found", "usuario")
        else:
            raise ValueCustomError("too_many_requests")
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except SendGridException as e:
        return handle_send_email_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
