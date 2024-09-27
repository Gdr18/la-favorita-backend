from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId
from pymongo import ReturnDocument, errors
from pydantic import ValidationError

from ..utils.db_utils import (
    db,
    extra_inputs_are_not_permitted,
    field_required,
    input_should_be
)
from ..models.user_model import UserModel


coll_users = db.users

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
        return (
            jsonify(
                msg=f"El usuario {new_user.inserted_id} ha sido añadido de forma satisfactoria"
            ),
            200,
        )
    except errors.DuplicateKeyError as e:
        return (
            jsonify(
                err=f"Error de clave duplicada en MongoDB: {e.details['keyValue']}"
            ),
            409,
        )
    except ValidationError as e:
        if "Extra inputs are not permitted" in str(e):
            return extra_inputs_are_not_permitted(e)
        elif "Field required" in str(e):
            return field_required(e, "name", "email", "password")
        elif "Value error" and "validate_password error" in str(e):
            return jsonify(err="La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-)"), 400
        elif "Value error" and "validate_phone error" in str(e):
            return jsonify(err="El teléfono debe tener el prefijo +34 y/o 9 dígitos, y debe ser tipo string."), 400
        elif "Input should be" in str(e):
            return input_should_be(e)
        else:
            return jsonify(err=f"Error: {e}"), 400
    except Exception as e:
        return jsonify(err=f"Error: Ha ocurrido un error inesperado: {e}"), 500


@user_route.route("/users", methods=["GET"])
def get_users():
    try:
        users = coll_users.find()
        response = json_util.dumps(users)
        return response, 200
    except Exception as e:
        return jsonify(err=f"Error: Ha ocurrido un error inesperado: {e}"), 500


@user_route.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
def manage_user(user_id):
    if request.method == "GET":
        try:
            user = coll_users.find_one({"_id": ObjectId(user_id)})
            if user:
                response = json_util.dumps(user)
                return response, 200
            else:
                return (
                    jsonify(err=f"Error: El usuario {user_id} no ha sido encontrado"),
                    404,
                )
        except Exception as e:
            return (
                jsonify(err=f"Error: Ha ocurrido un error inesperado: {e}"),
                500,
            )

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
                response = json_util.dumps(updated_user)
                return response
            else:
                return (
                    jsonify(err=f"Error: El usuario {user_id} no ha sido encontrado"),
                    404,
                )
        except errors.DuplicateKeyError as e:
            return (
                jsonify(
                    err=f"Error de clave duplicada en MongoDB: {e.details['keyValue']}"
                ),
                409,
            )
        except ValidationError as e:
            if "Extra inputs are not permitted" in str(e):
                return extra_inputs_are_not_permitted(e)
            elif "Value error" and "validate_password error" in str(e):
                return jsonify(err="La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-), y ser de tipo string"), 400
            elif "Value error" and "validate_phone error" in str(e):
                return jsonify(err="El teléfono debe tener el prefijo +34 y/o 9 dígitos, y ser de tipo string"), 400
            elif "Input should be" in str(e):
                return input_should_be(e)
            else:
                return jsonify(err=f"Error: {e}"), 400
        except Exception as e:
            return jsonify(err=f"Error: Ha ocurrido un error inesperado: {e}"), 500

    elif request.method == "DELETE":
        try:
            deleted_user = coll_users.delete_one({"_id": ObjectId(user_id)})
            if deleted_user.deleted_count > 0:
                return (
                    jsonify(
                        msg=f"El usuario {user_id} ha sido eliminado de forma satisfactoria"
                    ),
                    200,
                )
            else:
                return (
                    jsonify(err=f"Error: El usuario {user_id} no ha sido encontrado"),
                    404,
                )
        except Exception as e:
            return jsonify(err=f"Error: {e}"), 500
