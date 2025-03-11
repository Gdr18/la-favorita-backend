from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from src.models.user_model import UserModel
from src.services.security_service import revoke_access_token, delete_refresh_token
from src.utils.exception_handlers import handle_unexpected_error, handle_validation_error, ValueCustomError
from src.utils.mongodb_exception_handlers import handle_mongodb_exception
from src.utils.json_responses import success_json_response, db_json_response

users_resource = "usuario"

users_route = Blueprint("users", __name__)


@users_route.route("/", methods=["POST"])
@jwt_required()
def add_user() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    try:
        if not token_role == 0:
            raise ValueCustomError("not_authorized")
        user_data = request.get_json()
        user_object = UserModel(**user_data)
        new_user = user_object.insert_user()
        return success_json_response(new_user.inserted_id, users_resource, "añadido", 201)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@users_route.route("/", methods=["GET"])
@jwt_required()
def get_users() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    try:
        if not token_role <= 1:
            raise ValueCustomError("not_authorized")
        else:
            page = request.args.get("page", 1)
            per_page = request.args.get("per-page", 10)
            skip = (page - 1) * per_page
            users = UserModel.get_users(skip, per_page)
            return db_json_response(users)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@users_route.route("/<user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user(user_id: str) -> tuple[Response, int]:
    token = get_jwt()
    token_user_id = token["sub"]
    token_role = token["role"]
    try:
        if all([token_user_id != user_id, token_role <= 1]):
            raise ValueCustomError("not_authorized")
        if request.method == "GET":
            user = UserModel.get_user_by_user_id_without_id(user_id)
            if user:
                return db_json_response(user)
            else:
                raise ValueCustomError("not_found", users_resource)

        if request.method == "PUT":
            user = UserModel.get_user_by_user_id_without_id(user_id)
            if user:
                data = request.get_json()
                if all([data.get("role"), data.get("role") != user.get("role"), token_role != 1]):
                    raise ValueCustomError("not_authorized_to_set", "role")
                if all([data.get("email"), data.get("email") != user.get("email")]):
                    raise ValueCustomError("not_authorized_to_set", "email")
                combined_data = {**user, **data}
                user_object = UserModel(**combined_data)
                updated_user = user_object.update_user(user_id)
                return db_json_response(updated_user)
            else:
                raise ValueCustomError("not_found", users_resource)

        if request.method == "DELETE":
            deleted_user = UserModel.delete_user(user_id)
            if deleted_user.deleted_count > 0:
                revoke_access_token(token)
                delete_refresh_token(user_id)
                return success_json_response(token_user_id, users_resource, "eliminado")
            else:
                raise ValueCustomError("not_found", users_resource)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
