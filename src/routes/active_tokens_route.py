from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.token_model import TokenModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

active_tokens_resource = "token activo"

active_tokens_route = Blueprint("active_tokens", __name__)


@active_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_active_token() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_authorized")
    else:
        data = request.get_json()
        active_token = TokenModel(**data)
        active_token.insert_active_token()
        return success_json_response(active_tokens_resource, "añadido", 201)


@active_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_active_tokens() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_authorized")
    else:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per-page", 10))
        skip = (page - 1) * per_page
        active_tokens = TokenModel.get_active_tokens(skip, per_page)
        return db_json_response(active_tokens)


@active_tokens_route.route("/<active_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_active_token(active_token_id: str) -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_authorized")
    if request.method == "GET":
        active_token = TokenModel.get_active_token_by_token_id(active_token_id)
        if active_token:
            return db_json_response(active_token)
        else:
            raise ValueCustomError("not_found", active_tokens_resource)

    if request.method == "PUT":
        active_token = TokenModel.get_active_token_by_token_id(active_token_id)
        if active_token:
            data = request.get_json()
            mixed_data = {**active_token, **data}
            active_token_object = TokenModel(**mixed_data)
            active_token_updated = active_token_object.update_active_token(
                active_token_id
            )
            return db_json_response(active_token_updated)
        else:
            raise ValueCustomError("not_found", active_tokens_resource)

    if request.method == "DELETE":
        active_token_deleted = TokenModel.delete_active_token_by_token_id(
            active_token_id
        )
        if active_token_deleted.deleted_count > 0:
            return success_json_response(active_tokens_resource, "eliminado")
        else:
            raise ValueCustomError("not_found", active_tokens_resource)
