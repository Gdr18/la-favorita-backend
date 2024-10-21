from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from pymongo import errors, ReturnDocument
from pydantic import ValidationError
import pendulum

from ..models.revoked_token_model import RevokedTokenModel
from ..utils.db_utils import db
from ..utils.exceptions_management import handle_unexpected_error, ClientCustomError, handle_validation_error, handle_duplicate_key_error
from ..utils.successfully_responses import resource_msg, db_json_response

coll_tokens_revoked = db.revoked_tokens
tokens_revoked_resource = "token revocado"

token_revoked_route = Blueprint("revoked_token", __name__)


@token_revoked_route.route("/revoked_token", methods=["POST"])
@jwt_required()
def add_revoked_token():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(tokens_revoked_resource, "set")
        data = request.get_json()
        data["exp"] = pendulum.from_timestamp(data["exp"], tz="UTC")
        revoked_token = RevokedTokenModel(**data)
        new_revoked_token = coll_tokens_revoked.insert_one(revoked_token.to_dict())
        return resource_msg(new_revoked_token.inserted_id, tokens_revoked_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.json_response_not_authorized_set()
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@token_revoked_route.route("/revoked_tokens", methods=["GET"])
def get_revoked_tokens():
    try:
        # token_role = get_jwt().get("role")
        # if token_role != 1:
        #     raise ClientCustomError(tokens_revoked_resource, "get")
        revoked_tokens = coll_tokens_revoked.find()
        return db_json_response(revoked_tokens)
    except ClientCustomError as e:
        return e.json_response_not_authorized_access()
    except Exception as e:
        return handle_unexpected_error(e)


@token_revoked_route.route("/revoked_token/<revoked_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_revoked_token(revoked_token_id):
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(tokens_revoked_resource, "access")
        if request.method == "GET":
            revoked_token = coll_tokens_revoked.find_one({"_id": ObjectId(revoked_token_id)})
            if revoked_token:
                return db_json_response(revoked_token)
            else:
                raise ClientCustomError(tokens_revoked_resource, "not_found")

        # TODO: Comprobar como podría hacer PATCH para poder optimizar el rendimiento de la base de datos
        if request.method == "PUT":
            revoked_token = coll_tokens_revoked.find_one({"_id": ObjectId(revoked_token_id)}, {"_id": 0})
            if revoked_token:
                data = request.get_json()
                mixed_data = {**revoked_token, **data}
                data["exp"] = pendulum.parse(data["exp"])
                revoked_token_object = RevokedTokenModel(**mixed_data)
                updated_revoked_token = coll_tokens_revoked.find_one_and_update(
                    {"_id": ObjectId(revoked_token_id)},
                    {"$set": revoked_token_object.to_dict()},
                    return_document=ReturnDocument.AFTER,
                )
                return db_json_response(updated_revoked_token)
            else:
                raise ClientCustomError(tokens_revoked_resource, "not_found")

        if request.method == "DELETE":
            deleted_revoked_token = coll_tokens_revoked.delete_one({"_id": ObjectId(revoked_token_id)})
            if deleted_revoked_token.deleted_count > 0:
                return resource_msg(revoked_token_id, tokens_revoked_resource, "eliminado")
            else:
                raise ClientCustomError(tokens_revoked_resource, "not_found")
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
