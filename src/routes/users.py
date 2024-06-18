from flask import Blueprint, request


from ..utils.db import db, bcrypt

coll_users = db.users

user = Blueprint("user", __name__)


@user.route("/user", methods=["POST"])
def add_user():
    user_data = request.get_json()
    if user_data["name"] and user_data["password"] and user_data["email"]:
        user_data["password"] = bcrypt.generate_password_hash(
            user_data["password"]
        ).decode("utf-8")
        result = coll_users.insert_one(user_data)
    return f"The user {result.inserted_id} was added successfully"
