from flask_jwt_extended import create_access_token
from flask import jsonify
import pendulum

from ..models.revoked_token_model import RevokedTokenModel
from ..utils.exceptions_management import ClientCustomError
from ..utils.successfully_responses import resource_msg
from ..utils.db_utils import db, bcrypt, jwt


def login_user(user_data):
    user_request = db.users.find_one({"email": user_data.get("email")})
    if user_request:
        if bcrypt.check_password_hash(user_request.get("password"), user_data.get("password")):
            access_token = create_access_token(
                identity=str(user_request.get("_id")),
                additional_claims={"role": user_request.get("role")},
                fresh=True
            )
            return resource_msg(access_token, "token", "creado")
        raise ClientCustomError("password")
    else:
        raise ClientCustomError("email", "not_found")


def logout_user(token_jti, token_exp):
    token_exp = pendulum.from_timestamp(token_exp, tz="UTC")
    token_object = RevokedTokenModel(jti=token_jti, exp=token_exp)
    token_revoked = db.revoked_tokens.insert_one(token_object.to_dict())
    return resource_msg(token_revoked.inserted_id, "token revocado", "añadido", 201)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    check_token = db.revoked_tokens.find_one({"jti": jwt_payload.get("jti")})
    return True if check_token else None


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify(err="El token ha sido revocado. Por favor, inicie sesión de nuevo."), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify(err="El token ha expirado"), 401


@jwt.unauthorized_loader
def unauthorized_callback(error_message):
    return jsonify(err="Necesita un token autorizado para acceder a esta ruta."), 401
