from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import errors

from src.models.user_model import UserModel
from src.services.email_service import send_email
from src.services.security_service import revoke_access_token, delete_refresh_token
from src.utils.exceptions_management import (
    handle_unexpected_error,
    handle_validation_error,
    handle_duplicate_key_error,
    ClientCustomError,
)
from src.utils.successfully_responses import resource_msg, db_json_response

user_resource = "usuario"

user_route = Blueprint("user", __name__)


@user_route.route("/user", methods=["POST"])
def add_user():
    try:
        user_data = request.get_json()
        if user_data.get("role"):
            raise ClientCustomError("not_authorized_to_set_role")
        else:
            user_object = UserModel(**user_data)
            new_user = user_object.insert_user()
            send_email(new_user)
            return resource_msg(new_user.inserted_id, user_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@user_route.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    try:
        user_role = get_jwt().get("role")
        if user_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            users = UserModel.get_users()
            return db_json_response(users)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@user_route.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user(user_id):
    token = get_jwt()
    token_id = token["sub"]
    token_role = token["role"]
    try:
        if all([token_id != user_id, token_role != 1]):
            raise ClientCustomError("not_authorized")
        if request.method == "GET":
            user = UserModel.get_user_by_user_id(user_id)
            if user:
                return db_json_response(user)
            else:
                raise ClientCustomError("not_found", user_resource)

        if request.method == "PUT":
            user = UserModel.get_user_by_user_id(user_id)
            if user:
                data = request.get_json()
                if all([data.get("role"), data.get("role") != user.get("role"), token_role != 1]):
                    raise ClientCustomError("not_authorized_to_set_role")
                else:
                    if all([data.get("email"), data.get("email") != user.get("email")]):
                        data["confirmed"] = False
                    combined_data = {**user, **data}
                    user_object = UserModel(**combined_data)
                    updated_user = user_object.update_user(user_id)
                    if updated_user.get("email") != user.get("email"):
                        send_email(updated_user)
                    return db_json_response(updated_user)
            else:
                raise ClientCustomError("not_found", user_resource)

        if request.method == "DELETE":
            deleted_user = UserModel.delete_user(user_id)
            if deleted_user.deleted_count > 0:
                revoke_access_token(token)
                delete_refresh_token(user_id)
                return resource_msg(token_id, user_resource, "eliminado")
            else:
                raise ClientCustomError("not_found", user_resource)

    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
