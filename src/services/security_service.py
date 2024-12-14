from datetime import timedelta
from typing import Union

from authlib.integrations.flask_client import OAuth
from flask import jsonify, Response
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, decode_token

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from src.models.token_model import TokenModel
from src.services.db_services import db
from src.utils.exceptions_management import handle_unexpected_error
from src.utils.successfully_responses import resource_msg

bcrypt = Bcrypt()

jwt = JWTManager()
oauth = OAuth()

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def generate_access_token(user_data: dict) -> str:
    user_role = user_data.get("role")
    user_identity = user_data.get("_id")
    token_info = {
        "identity": str(user_identity),
        "additional_claims": {"role": user_role},
        "expires_delta": get_expiration_time_access_token(user_role),
    }
    access_token = create_access_token(**token_info)
    return access_token


def generate_refresh_token(user_data: dict) -> Union[str, tuple[Response, int]]:
    user_role = user_data.get("role")
    user_identity = user_data.get("_id")

    token_info = {"identity": str(user_identity), "expires_delta": get_expiration_time_refresh_token(user_role)}
    refresh_token = create_refresh_token(**token_info)

    refresh_token_decoded = decode_token(refresh_token)
    data_refresh_token_db = {
        "user_id": refresh_token_decoded.get("sub"),
        "jti": refresh_token_decoded.get("jti"),
        "expires_at": refresh_token_decoded.get("exp"),
    }
    try:
        TokenModel(**data_refresh_token_db).insert_refresh_token()
        return refresh_token
    except Exception as e:
        return handle_unexpected_error(e)


def generate_email_token(user_data: dict) -> Union[str, tuple[Response, int]]:
    user_identity = user_data.get("_id")
    token_info = {"identity": str(user_identity), "expires_delta": timedelta(days=1)}
    email_token = create_access_token(**token_info)
    decoded_token_email = decode_token(email_token)
    data_email_token_db = {
        "user_id": decoded_token_email.get("sub"),
        "jti": decoded_token_email.get("jti"),
        "expires_at": decoded_token_email.get("exp"),
    }
    try:
        TokenModel(**data_email_token_db).insert_email_token()
        return email_token
    except Exception as e:
        return handle_unexpected_error(e)


def get_expiration_time_access_token(role: int) -> timedelta:
    if role == 1:
        return timedelta(minutes=15)
    elif role == 2:
        return timedelta(hours=3)
    else:
        return timedelta(days=1)


def get_expiration_time_refresh_token(role: int) -> timedelta:
    if role == 1:
        return timedelta(hours=3)
    elif role == 2:
        return timedelta(hours=6)
    else:
        return timedelta(days=30)


def revoke_access_token(token: dict) -> tuple[Response, int]:
    token_object = TokenModel(user_id=token["sub"], jti=token["jti"], expires_at=token["exp"])
    token_revoked = token_object.insert_revoke_token()
    return resource_msg(token_revoked.inserted_id, "token revocado", "añadido", 201)


def delete_refresh_token(user_id: int) -> tuple[Response, int]:
    TokenModel.delete_refresh_token_by_user_id(user_id)
    return resource_msg(str(user_id), "refresh token del usuario", "eliminado")


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    check_token = db.revoked_tokens.find_one({"jti": jwt_payload.get("jti")})
    return True if check_token else None


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify(err="El token ha sido revocado"), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify(err="El token ha expirado"), 401


@jwt.unauthorized_loader
def unauthorized_callback(error_message):
    return jsonify(err="Necesita un token válido para acceder a esta ruta"), 401
