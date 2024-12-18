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

email_tokens_resource = "email token"

email_tokens_route = Blueprint("email_tokens", __name__)


@email_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_email_token():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            data = request.get_json()
            email_token = TokenModel(**data)
            new_email_token = email_token.insert_email_token()
            return resource_msg(new_email_token.inserted_id, email_tokens_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@email_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_email_tokens():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            email_tokens = TokenModel.get_email_tokens()
            return db_json_response(email_tokens)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@email_tokens_route.route("/<email_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_email_token(email_token_id):
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        if request.method == "GET":
            email_token = TokenModel.get_email_token_by_token_id(email_token_id)
            if email_token:
                return db_json_response(email_token)
            else:
                raise ClientCustomError("not_found", email_tokens_resource)
        if request.method == "PUT":
            email_token = TokenModel.get_email_token_by_token_id(email_token_id)
            if email_token:
                data = request.get_json()
                mixed_data = {**email_token, **data}
                email_token_object = TokenModel(**mixed_data)
                email_token_updated = email_token_object.update_email_token(email_token_id)
                return db_json_response(email_token_updated)
            else:
                raise ClientCustomError("not_found", email_tokens_resource)

        if request.method == "DELETE":
            email_token_deleted = TokenModel.delete_email_token(email_token_id)
            if email_token_deleted.deleted_count > 0:
                return resource_msg(email_token_id, email_tokens_resource, "eliminado")
            else:
                raise ClientCustomError("not_found", email_tokens_resource)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
