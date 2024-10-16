from flask_jwt_extended import create_access_token
from flask import jsonify

from ..utils.exceptions_management import ResourceNotFoundError
from ..utils.db_utils import db, bcrypt


class AuthService:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def login_user(self):
        user_request = db.users.find_one({"email": self.email})
        if user_request:
            if bcrypt.check_password_hash(user_request.get("password"), self.password):
                return self.generate_token(user_request)
            else:
                return jsonify(err="La contraseña no coincide"), 401
        else:
            raise ResourceNotFoundError(self.email, "usuario")

    @classmethod
    def generate_token(cls, user):
        access_token = create_access_token(
            identity={"id": str(user.get("_id")), "role": user.get("role")}
        )
        return jsonify(token=access_token), 200
