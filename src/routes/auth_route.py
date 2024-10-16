from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required


from ..utils.db_utils import db, bcrypt
from ..utils.exceptions_management import handle_unexpected_error, ResourceNotFoundError

auth_route = Blueprint("auth", __name__)

coll_users = db.users


@auth_route.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    try:
        user_request = coll_users.find_one({"email": data.get("email")})
        if user_request:
            if bcrypt.check_password_hash(user_request.get("password"), data.get("password")):
                access_token = create_access_token(
                    identity={"id": str(user_request["_id"]), "role": user_request["role"]}
                )
                return jsonify(access_token=access_token), 200
            else:
                return jsonify(err="La contraseña no coincide"), 401
        else:
            raise ResourceNotFoundError(data.get("email"), "usuario")
    except ResourceNotFoundError as e:
        return e.json_response()
    except Exception as e:
        return handle_unexpected_error(e)


@auth_route.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    pass
