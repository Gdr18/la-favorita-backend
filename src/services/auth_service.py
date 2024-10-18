from flask_jwt_extended import create_access_token
from flask import jsonify

from ..utils.exceptions_management import ClientCustomError
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
            return jsonify(token=access_token), 200
        raise ClientCustomError("password")
    else:
        raise ClientCustomError("email", "not_found")


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    token = db.revoked_tokens.find_one({"jti": jti})
    return token is not None


@jwt.revoked_token_loader
def revoked_token_callback():
    return jsonify({"err": "El token ha sido revocado. Por favor, inicie sesión de nuevo."}), 401
