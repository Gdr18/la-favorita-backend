from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from bson import ObjectId

from ..utils.db_utils import db, bcrypt

login = Blueprint("login", __name__)

coll = db["users"]


@login.route("/login", methods=["POST"])
def login():
    data = request.json.get()
    try:
        user_request = coll.find_one({"email": data.email})
        # TODO: Completar, refactorizar y comprobar
        if user_request:
            if data.email == "admin" and bcrypt.check_password_hash(
                user_request["password"], data.password
            ):
                access_token = create_access_token(
                    identity=ObjectId(user_request["_id"])
                )
                print(ObjectId(user_request["_id"]))
                return jsonify(access_token=access_token), 200
            else:
                return jsonify(message="Invalid username or password"), 401
        else:
            return jsonify(message="User not found"), 404
    except Exception as e:
        return jsonify(err=f"Error: {str(e)}"), 500
