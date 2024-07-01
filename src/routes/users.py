from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId, BSON
from pymongo import ReturnDocument, errors

from ..utils.db import db, bcrypt

coll_users = db.users
# coll_roles = db.roles

user = Blueprint("user", __name__)

@user.route("/user", methods=["POST"])
def add_user():
    user_data = request.get_json()
    if user_data.get("name") and user_data.get("password") and user_data.get("email"):
        user_data["password"] = bcrypt.generate_password_hash(
            user_data["password"]
        ).decode("utf-8")
        # TODO: AUTH usario tipo 1
        # if user_data.get("role") and not # usuario con rol tipo 1 :
        # return "No tiene autorización para asignar un rol."
        # else:
        # user_data["role"] = 3
        try:
            new_user = coll_users.insert_one(user_data)
            return f"El usuario {new_user.inserted_id} ha sido añadido satisfactoriamente."
        except errors.DuplicateKeyError as e:
            print(e)
            return f"Error de clave duplicada: {e.details['errmsg']}"
    else:
        raise TypeError("Alguna clave se ha olvidado o es inválida")


@user.route("/users", methods=["GET"])
def get_users():
    users = coll_users.find()
    response = json_util.dumps(users)
    return response


@user.route("/user/<user_id>", methods=["GET", "PUT", "DELETE"])
def manage_user(user_id):
    if request.method == "GET":
        user = coll_users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            return f"El usuario {user_id} no ha sido encontrado."
        else:
            # TODO: comprobar que funciona lo siguiente.
            response = BSON(user).as_dict()
            # response = json_util.dumps(user)
            return jsonify(response)

    elif request.method == "PUT":
        user_data = request.get_json()
        # if user_data.get("role") and not # usuario con rol tipo 1 :
        # return "No tiene autorización para modificar el rol."
        user_updated = coll_users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": user_data},
            return_document=ReturnDocument.AFTER,
        )
        if user_updated is None:
            return f"El usuario {user_id} no ha sido encontrado."
        else:
            # TODO: comprobar que funciona lo siguiente.
            response = BSON(user_updated).as_dict()
            # response = json_util.dumps(user_updated)
            return jsonify(response)

    elif request.method == "DELETE":
        user_deleted = coll_users.delete_one({"_id": ObjectId(user_id)})
        if user_deleted.deleted_count > 0:
            return f"El usuario {user_id} ha sido eliminado"
        else:
            return f"El usuario {user_id} no ha sido encontrado"
