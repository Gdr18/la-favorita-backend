from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId
from pymongo import ReturnDocument, errors

from ..utils.db import db, bcrypt
from ..models.user_model import User


coll_users = db.users

user = Blueprint("user", __name__)


# TODO: Testear los tipos de datos.
@user.route("/user", methods=["POST"])
def add_user():
    user_data = request.get_json()
    # TODO: AUTH usario tipo 1
    # if user_data.get("role") and not # usuario con rol tipo 1 :
    # return "No tiene autorización para asignar un rol."
    try:
        user_data["password"] = bcrypt.generate_password_hash(
            user_data["password"]
        ).decode("utf-8")
        user = User(**user_data).__dict__
        new_user = coll_users.insert_one(user)
        return (
            jsonify(
                {
                    "msg": f"El usuario {new_user.inserted_id} ha sido añadido satisfactoriamente."
                }
            ),
            200,
        )
    except errors.DuplicateKeyError as e:
        return (
            jsonify(
                {"err": f"Error de clave duplicada en MongoDB: {e.details['keyValue']}"}
            ),
            500,
        )
    except (KeyError, TypeError) as e:
        if str(e).startswith("User.__init__"):
            msg = str(e)[str(e).index(":") + 2 :].replace("and", "y")
            return (
                jsonify(
                    {
                        "err": f"Se ha olvidado: {msg}. Son requeridos: 'email', 'name' y 'password'."
                    }
                ),
                500,
            )
        else:
            return (
                jsonify(
                    {
                        "err": f"Se ha olvidado: {str(e)}. Son requeridos: 'email', 'name' y 'password'."
                    }
                ),
                500,
            )
    except:
        return jsonify({"err": "Ha ocurrido un error inesperado."}), 500


@user.route("/users", methods=["GET"])
def get_users():
    users = coll_users.find()
    response = json_util.dumps(users)
    return response, 200


@user.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
def manage_user(user_id):
    if request.method == "GET":
        user = coll_users.find_one({"_id": ObjectId(user_id)})
        if user:
            response = json_util.dumps(user)
            return response, 200
        else:
            return jsonify({"msg": f"El usuario {user_id} no ha sido encontrado."}), 404

    elif request.method == "PUT":
        user_data = coll_users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
        print(type(user_data))
        print(user_data)
        if user_data:
            for key, value in request.get_json().items():
                if key == "password":
                    # Confirmar cuando se realice el front que se necesita esta condicional.
                    if value != "" and not bcrypt.check_password_hash(
                        user_data["password"], value
                    ):
                        user_data["password"] = bcrypt.generate_password_hash(
                            value
                        ).decode("utf-8")
                elif (
                    key == "email" or key == "role"
                ):  # Falta añadir si el rol del que modifica es 1.
                    return jsonify({"msg": f"{key} no se puede modificar"}), 500
                else:
                    user_data[key] = value
            user_data = User(**user_data).__dict__
            # Para mejorar el rendimiento cuando se ponga a producción cambiar a update_one, o mirar si es realmente necesario.
            user_updated = coll_users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": user_data},
                return_document=ReturnDocument.AFTER,
            )
            response = json_util.dumps(user_updated)
            return response
        else:
            return jsonify({"msg": f"El usuario {user_id} no ha sido encontrado."}), 404

    elif request.method == "DELETE":
        user_deleted = coll_users.delete_one({"_id": ObjectId(user_id)})
        if user_deleted.deleted_count > 0:
            return jsonify({"msg": f"El usuario {user_id} ha sido eliminado."}), 200
        else:
            return jsonify({"msg": f"El usuario {user_id} no ha sido encontrado."}), 404
