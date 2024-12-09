from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import ReturnDocument, errors

from ..models.user_model import UserModel
from ..services.auth_service import revoke_token, generate_email_token
from ..services.email_service import send_email
from ..utils.db_utils import db
from ..utils.exceptions_management import (
    handle_unexpected_error,
    handle_validation_error,
    handle_duplicate_key_error,
    ClientCustomError,
    handle_email_not_valid_error,
)
from ..utils.successfully_responses import resource_msg, db_json_response

coll_users = db.users
user_resource = "usuario"

user_route = Blueprint("user", __name__)


@user_route.route("/user", methods=["POST"])
def add_user():
    try:
        user_data = request.get_json()
        # TODO: Si es mejor la validación del email de pydantic o de email_validator
        validate_email(user_data.get("email"))
        if user_data.get("role"):
            raise ClientCustomError("role")
        user_object = UserModel(**user_data)
        user_dict = user_object.to_dict()
        new_user = coll_users.insert_one(user_dict)
        if new_user:
            email_token = generate_email_token(user_dict)
            send_email(email_token, user_dict)
            return resource_msg(new_user.inserted_id, user_resource, "añadido", 201)
        raise Exception("Error al añadir el usuario")
    except ClientCustomError as e:
        return e.json_response_not_authorized_set()
    except EmailNotValidError as e:
        return handle_email_not_valid_error(e)
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
            raise ClientCustomError("usuarios", "access")
        users = coll_users.find()
        return db_json_response(users)
    except ClientCustomError as e:
        return e.json_response_not_authorized_access()
    except Exception as e:
        return handle_unexpected_error(e)


@user_route.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user(user_id):
    try:
        token_id = get_jwt().get("sub")
        token_role = get_jwt().get("role")
        if all([token_id != user_id, token_role != 1]):
            raise ClientCustomError(user_resource, "access")
        if request.method == "GET":
            user = coll_users.find_one({"_id": ObjectId(token_id)})
            if user:
                return db_json_response(user)
            else:
                raise ClientCustomError(user_resource, "not_found")

        if request.method == "PUT":
            user = coll_users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
            if user:
                data = request.get_json()
                if all([data.get("role"), data.get("role") != user.get("role"), token_role != 1]):
                    raise ClientCustomError("role", "change")
                # TODO: Combined_data dará problemas con eliminación de elementos de una lista o diccionario
                combined_data = {**user, **data}
                user_object = UserModel(**combined_data)
                if user_object.email != user["email"]:
                    validate_email(user_object.email)
                    user_object.confirmed = False
                # TODO: Para mejorar el rendimiento cuando se ponga a producción cambiar a update_one, o mirar si es realmente necesario
                updated_user = coll_users.find_one_and_update(
                    {"_id": ObjectId(user_id)}, {"$set": user_object.to_dict()}, return_document=ReturnDocument.AFTER
                )
                if updated_user and updated_user.get("email") != user.get("email"):
                    revoke_token(get_jwt())
                    email_token = generate_email_token(data)
                    send_email(email_token, user_object.to_dict())
                return db_json_response(updated_user)
            else:
                raise ClientCustomError(user_resource, "not_found")

        if request.method == "DELETE":
            # TODO: Revocar el refresh token del usuario eliminado
            deleted_user = coll_users.delete_one({"_id": ObjectId(user_id)})
            if deleted_user.deleted_count > 0:
                revoke_token(get_jwt())
                return resource_msg(token_id, user_resource, "eliminado")
            else:
                raise ClientCustomError(user_resource, "not_found")

    except ClientCustomError as e:
        if e.function == "not_found":
            return e.json_response_not_found()
        if e.function == "change":
            return e.json_response_not_authorized_change()
        if e.function == "access":
            return e.json_response_not_authorized_access()
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
