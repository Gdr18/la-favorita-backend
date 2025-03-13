from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt

from src.models.token_model import TokenModel
from src.utils.exception_handlers import ValueCustomError
from src.utils.json_responses import success_json_response, db_json_response

revoked_tokens_resource = "token revocado"

revoked_tokens_route = Blueprint("revoked_tokens", __name__)


@revoked_tokens_route.route("/", methods=["POST"])
@jwt_required()
def add_revoked_token() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_authorized")
    else:
        data = request.get_json()
        revoked_token = TokenModel(**data)
        new_revoked_token = revoked_token.insert_revoked_token()
        return success_json_response(new_revoked_token.inserted_id, revoked_tokens_resource, "añadido", 201)


@revoked_tokens_route.route("/", methods=["GET"])
@jwt_required()
def get_revoked_tokens() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_authorized")
    else:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per-page", 10))
        skip = (page - 1) * per_page
        revoked_tokens = TokenModel.get_revoked_tokens(skip, per_page)
        return db_json_response(revoked_tokens)


@revoked_tokens_route.route("/<revoked_token_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_revoked_token(revoked_token_id: str) -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role == 0:
        raise ValueCustomError("not_authorized")
    if request.method == "GET":
        revoked_token = TokenModel.get_revoked_token_by_token_id(revoked_token_id)
        if revoked_token:
            return db_json_response(revoked_token)
        else:
            raise ValueCustomError("not_found", revoked_tokens_resource)

    if request.method == "PUT":
        revoked_token = TokenModel.get_revoked_token_by_token_id(revoked_token_id)
        if revoked_token:
            data = request.get_json()
            mixed_data = {**revoked_token, **data}
            revoked_token_object = TokenModel(**mixed_data)
            revoked_token_updated = revoked_token_object.update_revoked_token(revoked_token_id)
            return db_json_response(revoked_token_updated)
        else:
            raise ValueCustomError("not_found", revoked_tokens_resource)

    if request.method == "DELETE":
        revoked_token_deleted = TokenModel.delete_revoked_token(revoked_token_id)
        if revoked_token_deleted.deleted_count > 0:
            return success_json_response(revoked_token_id, revoked_tokens_resource, "eliminado")
        else:
            raise ValueCustomError("not_found", revoked_tokens_resource)
