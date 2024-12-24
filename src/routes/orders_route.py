from flask import request, Blueprint, Response
from flask_jwt_extended import get_jwt, jwt_required
from pydantic import ValidationError

from src.models.order_model import OrderModel
from src.utils.successfully_responses import resource_msg, db_json_response
from src.utils.exceptions_management import ClientCustomError, handle_unexpected_error, handle_validation_error

orders_resource = "orden"
orders_route = Blueprint("orders", __name__)


@orders_route.route("/", methods=["POST"])
@jwt_required()
def insert_order() -> tuple[Response, int]:
    try:
        order_data = request.get_json()
        order_object = OrderModel(**order_data)
        inserted_order = order_object.insert_order()
        return resource_msg(inserted_order.inserted_id, orders_resource, "insertado")
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@orders_route.route("/")
@jwt_required()
def get_orders() -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        page = request.args.get("page", 1)
        per_page = request.args.get("per-page", 10)
        skip = (page - 1) * per_page
        orders = OrderModel.get_orders(per_page, skip)
        return db_json_response(orders)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@orders_route.route("/users/<user_id>")
@jwt_required()
def get_user_orders(user_id):
    try:
        token_id = get_jwt().get("sub")
        token_role = get_jwt().get("role")
        if not any([token_id == user_id, token_role == 1]):
            raise ClientCustomError("not_authorized")
        page = request.args.get("page", 1)
        per_page = request.args.get("per_page", 10)
        skip = (page - 1) * per_page
        user_orders = OrderModel.get_orders_by_user_id(user_id, skip, per_page)
        return db_json_response(user_orders)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@orders_route.route("/<order_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_order(order_id):
    token_id = get_jwt().get("sub")
    token_role = get_jwt().get("role")
    try:
        order = OrderModel.get_order(order_id)
        user_order = order.get("user_id")
        if not any([token_id == user_order, token_role == 1]):
            raise ClientCustomError("not_authorized")

        if request.method == "GET":
            return db_json_response(order)

        if request.method == "PUT":
            order_data = request.get_json()
            order_data_user_id = order_data.get("user_id")
            order_data_created_at = order_data.get("created_at")
            if all([order_data_user_id, order_data_user_id != user_order]):
                raise ClientCustomError("not_authorized_to_set", "user_id")
            if all([order_data_created_at, order_data_created_at != order.get("created_at")]):
                raise ClientCustomError("not_authorized_to_set", "created_at")
            mixed_data = {**order, **order_data}
            order_object = OrderModel(**mixed_data)
            updated_order = order_object.update_order(order_id)
            return db_json_response(updated_order)

        if request.method == "DELETE":
            if not order:
                raise ClientCustomError("not_found", orders_resource)
            OrderModel.delete_order(order_id)
            return resource_msg(order_id, orders_resource, "eliminado")

    except ClientCustomError as e:
        return e.response
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
