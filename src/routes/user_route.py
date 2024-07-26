from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId
from pymongo import ReturnDocument, errors

from ..utils.db_utils import (
    db,
    bcrypt,
    unexpected_keyword_argument,
    required_positional_argument,
)
from ..models.user_model import UserModel


coll_users = db.users

user = Blueprint("user", __name__)


@user.route("/user", methods=["POST"])
def add_user():
    try:
        user_data = request.get_json()
        # TODO: AUTH usario tipo 1
        # if user_data.get("role") and not # usuario con rol tipo 1 :
        # raise "No tiene autorización para asignar un rol."
        user = UserModel(**user_data).__dict__
        # user["password"] = bcrypt.generate_password_hash(user["password"]).decode(
        #     "utf-8"
        # )
        user.hashing_password()
        new_user = coll_users.insert_one(user)
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
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            return unexpected_keyword_argument(e)
        elif "required positional argument" in str(e):
            return required_positional_argument(e, "name", "email", "password")
        else:
            return jsonify(err=f"Error: {e}"), 400
    except ValueError as e:
        return jsonify(err=f"Error: {e}"), 400
    except Exception as e:
        return jsonify(err=f"Error: Ha ocurrido un error inesperado: {e}"), 500


@user.route("/users", methods=["GET"])
def get_users():
    try:
        users = coll_users.find()
        response = json_util.dumps(users)
        return response, 200
    except Exception as e:
        return jsonify(err=f"Error: Ha ocurrido un error inesperado: {e}"), 500


@user.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
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
                for key, value in request.get_json().items():
                    if key == "password":
                        # TODO: Confirmar cuando se realice el front que se necesita esta condicional
                        if value != "" and not bcrypt.check_password_hash(
                            user["password"], value
                        ):
                        # TODO: No se hace la comprobación del tipo de dato de la contraseña desde el modelo
                            user["password"] = bcrypt.generate_password_hash(
                                value
                            ).decode("utf-8")
                    elif (
                        key == "email" or key == "role"
                    ):  # TODO: Falta añadir si el rol del que modifica es 1
                        return (
                            jsonify(err=f"Error: {key} no se puede modificar"),
                            500,
                        )
                    else:
                        user[key] = value
                user_data = UserModel(**user).__dict__
                # TODO: Para mejorar el rendimiento cuando se ponga a producción cambiar a update_one, o mirar si es realmente necesario
                updated_user = coll_users.find_one_and_update(
                    {"_id": ObjectId(user_id)},
                    {"$set": user_data},
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
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                return unexpected_keyword_argument(e)
            else:
                return jsonify(err=f"Error: {e}"), 400
        except Exception as e:
            return jsonify(err=f"Error: {e}"), 500

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
