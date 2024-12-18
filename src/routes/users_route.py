from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import errors

from src.models.user_model import UserModel
from src.services.security_service import revoke_access_token, delete_refresh_token
from src.utils.exceptions_management import (
    handle_unexpected_error,
    handle_validation_error,
    handle_duplicate_key_error,
    ClientCustomError,
)
from src.utils.successfully_responses import resource_msg, db_json_response

users_resource = "usuario"

users_route = Blueprint("users", __name__)


@users_route.route("/", methods=["POST"])
@jwt_required()
def add_user():
    token_role = get_jwt().get("role")
    try:
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        user_data = request.get_json()
        user_object = UserModel(**user_data)
        new_user = user_object.insert_user()
        return resource_msg(new_user.inserted_id, users_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@users_route.route("/", methods=["GET"])
@jwt_required()
def get_users():
    token_role = get_jwt().get("role")
    try:
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            users = UserModel.get_users()
            return db_json_response(users)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@users_route.route("/<user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user(user_id):
    token = get_jwt()
    token_user_id = token["sub"]
    token_role = token["role"]
    try:
        if all([token_user_id != user_id, token_role != 1]):
            raise ClientCustomError("not_authorized")
        if request.method == "GET":
            user = UserModel.get_user_by_user_id(user_id)
            if user:
                return db_json_response(user)
            else:
                raise ClientCustomError("not_found", users_resource)

        if request.method == "PUT":
            user = UserModel.get_user_by_user_id(user_id)
            if user:
                data = request.get_json()
                if all([data.get("role"), data.get("role") != user.get("role"), token_role != 1]):
                    raise ClientCustomError("not_authorized_to_set_role")
                if all([data.get("email"), data.get("email") != user.get("email")]):
                    # TODO: Hacer una respuesta en ClientCustomError para este caso?
                    raise Exception("No puede cambiar el email")
                combined_data = {**user, **data}
                user_object = UserModel(**combined_data)
                updated_user = user_object.update_user(user_id)
                return db_json_response(updated_user)
            else:
                raise ClientCustomError("not_found", users_resource)

        if request.method == "DELETE":
            deleted_user = UserModel.delete_user(user_id)
            if deleted_user.deleted_count > 0:
                revoke_access_token(token)
                delete_refresh_token(user_id)
                return resource_msg(token_user_id, users_resource, "eliminado")
            else:
                raise ClientCustomError("not_found", users_resource)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
