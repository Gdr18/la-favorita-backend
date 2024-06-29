from flask import Blueprint, request
from bson import json_util, ObjectId
from pymongo.collection import ReturnDocument

from ..utils.db import db, bcrypt

coll_users = db.users
coll_roles = db.roles

user = Blueprint("user", __name__)

def checking_role(user_email):
    role = coll_roles.find({"email": user_email})
    if role:
        return role.type
    else:
        return 3

# Falta testear comportamiento función y endpoints POST y PUT
@user.route("/user", methods=["POST"])
def add_user():
    user_data = request.get_json()
    if user_data.get("name") and user_data.get("password") and user_data.get("email"):
        user_data["password"] = bcrypt.generate_password_hash(
            user_data["password"]
        ).decode("utf-8")
        user_data["role"] = checking_role(user_data["email"])
        new_user = coll_users.insert_one(user_data)
        return f"The user {new_user.inserted_id} was added successfully"
    else:
        raise TypeError("Some key is missing or invalid")


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
            return f"The user {user_id} was not found"
        else:
            response = json_util.dumps(user)
            return response

    elif request.method == "PUT":
        user_data = request.get_json()
        user_data["role"] = checking_role(user_data["email"])
        user_updated = coll_users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": user_data},
            return_document=ReturnDocument.AFTER,
        )
        if user_updated is None:
            return f"The user {user_id} was not found"
        else:
            response = json_util.dumps(user_updated)
            return response

    elif request.method == "DELETE":
        user_deleted = coll_users.delete_one({"_id": ObjectId(user_id)})
        if user_deleted.deleted_count is 1:
            return f"The user {user_id} was deleted"
        else:
            return f"The user {user_id} was not found"
