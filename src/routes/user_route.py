from flask import Blueprint, request
from bson import ObjectId
from pymongo import ReturnDocument, errors
from pydantic import ValidationError
from flask_jwt_extended import jwt_required, get_jwt

from ..utils.db_utils import db
from ..utils.exceptions_management import handle_unexpected_error, handle_validation_error, handle_duplicate_key_error, ClientCustomError
from ..utils.successfully_responses import resource_added_msg, resource_deleted_msg, db_json_response

from ..models.user_model import UserModel

coll_users = db.users
user_resource = "usuario"

user_route = Blueprint("user", __name__)


@user_route.route("/user", methods=["POST"])
def add_user():
    try:
        user_data = request.get_json()
        if user_data.get("role"):
            raise ClientCustomError("role")
        user_object = UserModel(**user_data)
        new_user = coll_users.insert_one(user_object.to_dict())
        return resource_added_msg(new_user.inserted_id, user_resource)
    except ClientCustomError as e:
        return e.json_response_not_authorized_set()
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
        users = coll_users.find()
        return db_json_response(users)
    except Exception as e:
        return handle_unexpected_error(e)


@user_route.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def manage_user(user_id):
    if request.method == "GET":
        try:
            user = coll_users.find_one({"_id": ObjectId(user_id)})
            if user:
                return db_json_response(user)
            else:
                raise ClientCustomError(user_resource, user_id)
        except ClientCustomError as e:
            return e.json_response_not_found()
        except Exception as e:
            return handle_unexpected_error(e)

    if request.method == "PUT":
        try:
            user_token = get_jwt()
            if user_token.get("sub") != user_id or user_token.get("role") != 1:
                raise ClientCustomError("usuario")
            user = coll_users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
            if user:
                data = request.get_json()
                print(user_token)
                print(user_token.get("role"))
                if user_token.get("role") != 1 and data.get("role") != user.get("role"):
                    raise ClientCustomError("role")
                combined_data = {**user, **data}
                user_object = UserModel(**combined_data)
                # TODO: Para mejorar el rendimiento cuando se ponga a producción cambiar a update_one, o mirar si es realmente necesario
                updated_user = coll_users.find_one_and_update(
                    {"_id": ObjectId(user_id)},
                    {"$set": user_object.to_dict()},
                    return_document=ReturnDocument.AFTER,
                )
                return db_json_response(updated_user)
            else:
                raise ClientCustomError(user_id, user_resource)
        except ClientCustomError as e:
            if e.data_resource:
                return e.json_response_not_found()
            if any([e.resource == "usuario", e.resource == "role"]):
                return e.json_response_not_authorized_change()
        except errors.DuplicateKeyError as e:
            return handle_duplicate_key_error(e)
        except ValidationError as e:
            return handle_validation_error(e)
        except Exception as e:
            return handle_unexpected_error(e)

    if request.method == "DELETE":
        try:
            deleted_user = coll_users.delete_one({"_id": ObjectId(user_id)})
            if deleted_user.deleted_count > 0:
                return resource_deleted_msg(user_id, user_resource)
            else:
                raise ClientCustomError(user_resource, user_id)
        except ClientCustomError as e:
            return e.json_response_not_found()
        except Exception as e:
            return handle_unexpected_error(e)
