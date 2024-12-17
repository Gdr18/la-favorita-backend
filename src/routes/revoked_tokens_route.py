from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import errors

from src.models.token_model import TokenModel
from src.utils.exceptions_management import (
    handle_unexpected_error,
    ClientCustomError,
    handle_validation_error,
    handle_duplicate_key_error,
)
from src.utils.successfully_responses import resource_msg, db_json_response

revoked_tokens_resource = "token revocado"

revoked_tokens_route = Blueprint("revoked_tokens", __name__)


@revoked_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_revoked_token():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            data = request.get_json()
            revoked_token = TokenModel(**data)
            new_revoked_token = revoked_token.insert_revoke_token()
            return resource_msg(new_revoked_token.inserted_id, revoked_tokens_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@revoked_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_revoked_tokens():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            revoked_tokens = TokenModel.get_revoke_tokens()
            return db_json_response(revoked_tokens)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@revoked_tokens_route.route("/<revoked_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_revoked_token(revoked_token_id):
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        if request.method == "GET":
            revoked_token = TokenModel.get_revoke_token_by_token_id(revoked_token_id)
            if revoked_token:
                return db_json_response(revoked_token)
            else:
                raise ClientCustomError("not_found", revoked_tokens_resource)

        if request.method == "PUT":
            revoked_token = TokenModel.get_revoke_token_by_token_id(revoked_token_id)
            if revoked_token:
                data = request.get_json()
                mixed_data = {**revoked_token, **data}
                revoked_token_object = TokenModel(**mixed_data)
                revoked_token_updated = revoked_token_object.update_revoke_token(revoked_token_id)
                return db_json_response(revoked_token_updated)
            else:
                raise ClientCustomError("not_found", revoked_tokens_resource)

        if request.method == "DELETE":
            revoked_token_deleted = TokenModel.delete_revoke_token(revoked_token_id)
            if revoked_token_deleted.deleted_count > 0:
                return resource_msg(revoked_token_id, revoked_tokens_resource, "eliminado")
            else:
                raise ClientCustomError("not_found", revoked_tokens_resource)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
