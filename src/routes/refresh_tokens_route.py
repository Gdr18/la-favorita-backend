from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from src.models.token_model import TokenModel
from src.utils.exceptions_management import (
    handle_unexpected_error,
    ClientCustomError,
    handle_validation_error,
    handle_duplicate_key_error,
)
from src.utils.successfully_responses import resource_msg, db_json_response

refresh_tokens_resource = "refresh token"

refresh_tokens_route = Blueprint("refresh_tokens", __name__)


@refresh_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_refresh_token() -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role == 0:
            raise ClientCustomError("not_authorized")
        else:
            data = request.get_json()
            refresh_token = TokenModel(**data)
            new_refresh_token = refresh_token.insert_refresh_token()
            return resource_msg(new_refresh_token.inserted_id, refresh_tokens_resource, "añadido", 201)
    except ClientCustomError as e:
        return e.response
    except DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@refresh_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_refresh_tokens() -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role == 0:
            raise ClientCustomError("not_authorized")
        else:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per-page", 10))
            skip = (page - 1) * per_page
            refresh_tokens = TokenModel.get_refresh_tokens(skip, per_page)
            return db_json_response(refresh_tokens)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@refresh_tokens_route.route("/<refresh_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_refresh_token(refresh_token_id: str) -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role == 0:
            raise ClientCustomError("not_authorized")
        if request.method == "GET":
            refresh_token = TokenModel.get_refresh_token_by_token_id(refresh_token_id)
            if refresh_token:
                return db_json_response(refresh_token)
            raise ClientCustomError("not_found", refresh_tokens_resource)

        if request.method == "PUT":
            refresh_token = TokenModel.get_refresh_token_by_token_id(refresh_token_id)
            if refresh_token:
                data = request.get_json()
                mixed_data = {**refresh_token, **data}
                refresh_token_object = TokenModel(**mixed_data)
                refresh_token_updated = refresh_token_object.update_refresh_token(refresh_token_id)
                return db_json_response(refresh_token_updated)
            else:
                raise ClientCustomError("not_found", refresh_tokens_resource)

        if request.method == "DELETE":
            refresh_token_deleted = TokenModel.delete_refresh_token_by_token_id(refresh_token_id)
            if refresh_token_deleted.deleted_count > 0:
                return resource_msg(refresh_token_id, refresh_tokens_resource, "eliminado")
            else:
                raise ClientCustomError("not_found", refresh_tokens_resource)
    except ClientCustomError as e:
        return e.response
    except DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
