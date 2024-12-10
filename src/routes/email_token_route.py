from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import errors

from ..models.token_model import TokenModel
from ..utils.exceptions_management import (
    handle_unexpected_error,
    ClientCustomError,
    handle_validation_error,
    handle_duplicate_key_error,
)
from ..utils.successfully_responses import resource_msg, db_json_response

email_tokens_resource = "email token"

email_token_route = Blueprint("email_token", __name__)


@email_token_route.route("/email_token", methods=["POST"])
@jwt_required()
def add_email_token():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(email_tokens_resource, "set")
        data = request.get_json()
        email_token = TokenModel(**data)
        new_email_token = email_token.insert_email_token()
        return resource_msg(new_email_token.inserted_id, email_tokens_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.json_response_not_authorized_set()
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@email_token_route.route("/email_tokens", methods=["GET"])
@jwt_required()
def get_email_tokens():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(email_tokens_resource, "get")
        email_tokens = TokenModel.get_email_tokens()
        return db_json_response(email_tokens)
    except ClientCustomError as e:
        return e.json_response_not_authorized_access()
    except Exception as e:
        return handle_unexpected_error(e)


@email_token_route.route("/email_token/<email_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_email_token(email_token_id):
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError(email_tokens_resource, "access")
        if request.method == "GET":
            email_token = TokenModel.get_email_token(email_token_id)
            if email_token:
                return db_json_response(email_token)
            else:
                raise ClientCustomError(email_tokens_resource, "not_found")

        # TODO: Comprobar como podría hacer PATCH para poder optimizar el rendimiento de la base de datos
        if request.method == "PUT":
            email_token = TokenModel.get_email_token(email_token_id)
            if email_token:
                data = request.get_json()
                mixed_data = {**email_token, **data}
                email_token_object = TokenModel(**mixed_data)
                email_token_updated = email_token_object.update_email_token(email_token_id)
                return db_json_response(email_token_updated)
            else:
                raise ClientCustomError(email_tokens_resource, "not_found")

        if request.method == "DELETE":
            email_token_deleted = TokenModel.delete_email_token(email_token_id)
            if email_token_deleted.deleted_count > 0:
                return resource_msg(email_token_id, email_tokens_resource, "eliminado")
            else:
                raise ClientCustomError(email_tokens_resource, "not_found")
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
