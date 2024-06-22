from flask import Blueprint, request
from bson import json_util

from ..utils.db import db

coll_roles = db.roles

role = Blueprint("role", __name__)


@role.route("/role", methods=["POST"])
def add_role():
    role_data = request.get_json()
    if role_data.get("type") and role_data.get("email"):
        role = coll_roles.insert_one(role_data)
        return f"The role with the id {role.inserted_id} was added"
    else:
        raise TypeError("Some key is missing or invalid")


@role.route("/roles", methods=["GET"])
def get_roles():
    roles = coll_roles.find()
    response = json_util.dumps(roles)
    return response
