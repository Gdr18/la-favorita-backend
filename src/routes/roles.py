from flask import Blueprint, request
from bson import json_util, ObjectId
from pymongo.collection import ReturnDocument

from ..utils.db import db

coll_roles = db.roles
coll_users = db.users

role = Blueprint("role", __name__)


# La siguiente función no está testeada ni los endpoints POST y PUT
def checking_user(role_id):
    role = coll_roles.find(role_id)
    user = coll_users.find(role.email)
    if user:
        if user.role != role.type:
            user_updated = coll_users.update_one(
                {"email": user.email}, {"$set": {"role": role.type}}
            )
            return f"the user {user_updated._id} was updated"
        else:
            return f"the user {user._id} was not updated"
    else:
        return f"the user was not found"


@role.route("/role", methods=["POST"])
def add_role():
    role_data = request.get_json()
    if role_data.get("email") and role_data.get("type"):
        role = coll_roles.insert_one(role_data)
        checking = checking_user(role.inserted_id)
        return f"The role {role.inserted_id} was added successfully and {checking}"
    else:
        raise TypeError("Some key is missing or invalid")


@role.route("/roles", methods=["GET"])
def get_roles():
    roles = coll_roles.find()
    response = json_util.dumps(roles)
    return response


@role.route("/role/<role_id>", methods=["GET", "PUT", "DELETE"])
def manage_role(role_id):
    if request.method == "GET":
        role = coll_roles.find_one({"_id": ObjectId(role_id)})
        if role is None:
            return f"The role {role_id} was not found"
        else:
            response = json_util.dumps(role)
            return response

    elif request.method == "PUT":
        role_data = request.get_json()
        role_updated = coll_roles.find_one_and_update(
            {"_id": ObjectId(role_id)},
            {"$set": role_data},
            return_document=ReturnDocument.AFTER,
        )
        if role_updated is None:
            return f"The role {role_id} was not found"
        else:
            checking = checking_user(role_id)
            response = json_util.dumps(role_updated)
            return f"The document of the role updated is {response} and {checking}" response

    elif request.method == "DELETE":
        role_deleted = coll_roles.delete_one({"_id": ObjectId(role_id)})
        if role_deleted.deleted_count is 1:
            return f"The role {role_id} was deleted"
        else:
            return f"The role {role_id} was not found"
