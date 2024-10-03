from flask import Blueprint, request
from bson import ObjectId
from pymongo import ReturnDocument, errors
from pydantic import ValidationError

from ..utils.db_utils import db
from ..utils.exceptions_management import handle_unexpected_error, handle_validation_error, handle_duplicate_key_error, ResourceNotFoundError
from ..models.user_model import UserModel
from ..utils.successfully_responses import resource_added_msg, resource_deleted_msg, db_json_response


coll_users = db.users
user_resource = "usuario"

user_route = Blueprint("user", __name__)


@user_route.route("/user", methods=["POST"])
def add_user():
    try:
        user_data = request.get_json()
        # TODO: AUTH usuario tipo 1
        # if user_data.get("role") and not # usuario con rol tipo 1 :
        # raise "No tiene autorización para asignar un rol."
        user_object = UserModel(**user_data)
        new_user = coll_users.insert_one(user_object.to_dict())
        return resource_added_msg(new_user.inserted_id, user_resource)
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@user_route.route("/users", methods=["GET"])
def get_users():
    try:
        users = coll_users.find()
        return db_json_response(users)
    except Exception as e:
        return handle_unexpected_error(e)


@user_route.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
def manage_user(user_id):
    if request.method == "GET":
        try:
            user = coll_users.find_one({"_id": ObjectId(user_id)})
            if user:
                return db_json_response(user)
            else:
                raise ResourceNotFoundError(user_id, user_resource)
        except ResourceNotFoundError as e:
            return e.json_response()
        except Exception as e:
            return handle_unexpected_error(e)

    elif request.method == "PUT":
        try:
            user = coll_users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
            if user:
                data = request.get_json()
                # TODO: Mirar cómo se podría cambiar el email también?
                # TODO: AUTH usuario tipo 1: if (data.get("role") or data.get("email")) and not # usuario con rol tipo 1: raise "No tiene autorización para asignar un rol o cambiar el email."
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
                raise ResourceNotFoundError(user_id, user_resource)
        except ResourceNotFoundError as e:
            return e.json_response()
        except errors.DuplicateKeyError as e:
            return handle_duplicate_key_error(e)
        except ValidationError as e:
            return handle_validation_error(e)
        except Exception as e:
            return handle_unexpected_error(e)

    elif request.method == "DELETE":
        try:
            deleted_user = coll_users.delete_one({"_id": ObjectId(user_id)})
            if deleted_user.deleted_count > 0:
                return resource_deleted_msg(user_id, user_resource)
            else:
                raise ResourceNotFoundError(user_id, user_resource)
        except ResourceNotFoundError as e:
            return e.json_response()
        except Exception as e:
            return handle_unexpected_error(e)
