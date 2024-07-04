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
    # if user_data.get("name") and user_data.get("password") and user_data.get("email"):
    # user_data["password"] = bcrypt.generate_password_hash(
    #     user_data.get("password")
    # ).decode("utf-8")
    # print(user_data)
    # TODO: AUTH usario tipo 1
    # if user_data.get("role") and not # usuario con rol tipo 1 :
    # return "No tiene autorización para asignar un rol."
    # else:
    # user_data["role"] = 3
    try:
        user_data["password"] = bcrypt.generate_password_hash(
            user_data["password"]
        ).decode("utf-8")
        user = User(**user_data).__dict__
        new_user = coll_users.insert_one(user)
        return f"El usuario {new_user.inserted_id} ha sido añadido satisfactoriamente."
    except errors.DuplicateKeyError as e:
        return (
            jsonify({"err": f"Error de clave duplicada: {e.details['keyValue']}"}),
            500,
        )
    # TODO: Mejorar la gestión de errores.
    except KeyError as e:
        print(e, "KeyError")
        return jsonify({"err": f"Se ha olvidado {e}"}), 500
    except TypeError as e:
        print(e, "TypeError")
        msg = str(e)[str(e).index(":"):].replace("and", "y")
        print(msg)
        return jsonify({"err": f"Se ha olvidado{msg}"}), 500



@user.route("/users", methods=["GET"])
def get_users():
    users = coll_users.find()
    response = json_util.dumps(users)
    print(type(response))
    return response


@user.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
def manage_user(user_id):
    if request.method == "GET":
        user = coll_users.find_one({"_id": ObjectId(user_id)})
        print(type(user), "usuario")
        if user:
            response = json_util.dumps(user)
            return response
        else:
            print(
                type(jsonify({"msg": f"El usuario {user_id} no ha sido encontrado."})),
                "jsonify",
            )
            return jsonify({"msg": f"El usuario {user_id} no ha sido encontrado."}), 404

    elif request.method == "PUT":
        user_data = coll_users.find_one({"_id": ObjectId(user_id)}, {"_id": -1})
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
                elif key == "role" or key == "email":
                    return jsonify({"msg": f"El {key} no se puede modificar"}), 500
                else:
                    user_data[key] = value
            user_data = User(**user_data).__dict__
            # Para mejorar el rendimiento cuando se ponga a producción cambiar a update_one
            user_updated = coll_users.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": user},
                return_document=ReturnDocument.AFTER,
            )
            response = json_util.dumps(user_updated)
            return response
        else:
            return f"El usuario {user_id} no ha sido encontrado."

    elif request.method == "DELETE":
        user_deleted = coll_users.delete_one({"_id": ObjectId(user_id)})
        if user_deleted.deleted_count > 0:
            return f"El usuario {user_id} ha sido eliminado."
        else:
            return jsonify({"msg": f"El usuario {user_id} no ha sido encontrado."}), 404
