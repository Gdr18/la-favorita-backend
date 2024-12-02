from bson import ObjectId
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import errors, ReturnDocument

from ..models.token_model import TokenModel
from ..utils.db_utils import db
from ..utils.exceptions_management import (
    handle_unexpected_error,
    ClientCustomError,
    handle_validation_error,
    handle_duplicate_key_error,
)
from ..utils.successfully_responses import resource_msg, db_json_response

coll_refresh_tokens = db.refresh_tokens
refresh_tokens_resource = "refresh token"

refresh_token_route = Blueprint("refresh_token", __name__)


@refresh_token_route.route("/refresh_token", methods=["POST"])
@jwt_required()
def add_refresh_token():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(refresh_tokens_resource, "set")
        data = request.get_json()
        refresh_token = TokenModel(**data)
        new_refresh_token = coll_refresh_tokens.insert_one(refresh_token.to_dict())
        return resource_msg(new_refresh_token.inserted_id, refresh_tokens_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.json_response_not_authorized_set()
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@refresh_token_route.route("/refresh_tokens", methods=["GET"])
@jwt_required()
def get_refresh_tokens():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(refresh_tokens_resource, "get")
        refresh_tokens = coll_refresh_tokens.find()
        return db_json_response(refresh_tokens)
    except ClientCustomError as e:
        return e.json_response_not_authorized_access()
    except Exception as e:
        return handle_unexpected_error(e)


@refresh_token_route.route("/refresh_token/<refresh_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_refresh_token(refresh_token_id):
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(refresh_tokens_resource, "access")
        if request.method == "GET":
            refresh_token = coll_refresh_tokens.find_one({"_id": ObjectId(refresh_token_id)})
            if refresh_token:
                return db_json_response(refresh_token)
            else:
                raise ClientCustomError(refresh_tokens_resource, "not_found")

        # TODO: Comprobar como podría hacer PATCH para poder optimizar el rendimiento de la base de datos
        if request.method == "PUT":
            refresh_token = coll_refresh_tokens.find_one({"_id": ObjectId(refresh_token_id)}, {"_id": 0})
            if refresh_token:
                data = request.get_json()
                mixed_data = {**refresh_token, **data}
                refresh_token_object = TokenModel(**mixed_data)
                refresh_token_updated = coll_refresh_tokens.find_one_and_update(
                    {"_id": ObjectId(refresh_token_id)},
                    {"$set": refresh_token_object.to_dict()},
                    return_document=ReturnDocument.AFTER,
                )
                return db_json_response(refresh_token_updated)
            else:
                raise ClientCustomError(refresh_tokens_resource, "not_found")

        if request.method == "DELETE":
            refresh_token_deleted = coll_refresh_tokens.delete_one({"_id": ObjectId(refresh_token_id)})
            if refresh_token_deleted.deleted_count > 0:
                return resource_msg(refresh_token_id, refresh_tokens_resource, "eliminado")
            else:
                raise ClientCustomError(refresh_tokens_resource, "not_found")
    except ClientCustomError as e:
        if e.function == "not_found":
            return e.json_response_not_found()
        if e.function == "access":
            return e.json_response_not_authorized_access()
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
