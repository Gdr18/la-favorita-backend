from flask import request, Blueprint, Response
from flask_jwt_extended import get_jwt, jwt_required
from pymongo.errors import PyMongoError

from src.models.order_model import OrderModel
from src.models.product_model import ProductModel
from src.utils.json_responses import success_json_response, db_json_response
from src.utils.exception_handlers import ValueCustomError
from src.services.db_service import client

orders_resource = "orden"
orders_route = Blueprint("orders", __name__)


@orders_route.route("/", methods=["POST"])
@jwt_required()
def add_order() -> tuple[Response, int]:
    order_data = request.get_json()
    order_object = OrderModel(**order_data)
    inserted_order = order_object.insert_order()
    return success_json_response(
        inserted_order.inserted_id, orders_resource, "insertado", 201
    )


@orders_route.route("/")
@jwt_required()
def get_orders() -> tuple[Response, int]:
    token_role = get_jwt().get("role")
    if not token_role <= 1:
        raise ValueCustomError("not_authorized")
    page = request.args.get("page", 1)
    per_page = request.args.get("per-page", 10)
    skip = (page - 1) * per_page
    orders = OrderModel.get_orders(skip, per_page)
    return db_json_response(orders)


@orders_route.route("/users/<user_id>")
@jwt_required()
def get_user_orders(user_id):
    token_data = get_jwt()
    token_id = token_data.get("sub")
    token_role = token_data.get("role")
    if not any([token_id == user_id, token_role <= 1]):
        raise ValueCustomError("not_authorized")
    page = request.args.get("page", 1)
    per_page = request.args.get("per_page", 10)
    skip = (page - 1) * per_page
    user_orders = OrderModel.get_orders_by_user_id(user_id, skip, per_page)
    return db_json_response(user_orders)


@orders_route.route("/<order_id>", methods=["PUT"])
@jwt_required()
def update_order(order_id):
    session = client.start_session()
    token_data = get_jwt()
    token_id = token_data.get("sub")
    token_role = token_data.get("role")
    order = OrderModel.get_order(order_id)
    if not order:
        raise ValueCustomError("not_found", orders_resource)
    user_order = order.get("user_id")
    if not any([token_id == user_order, token_role <= 1]):
        raise ValueCustomError("not_authorized")
    order_new_data = request.get_json()
    if order_new_data.get("state") and order["state"] != order_new_data.get("state"):
        OrderModel.check_level_state(order_new_data.get("state"), order["state"])
    order_mixed_data = {**order, **order_new_data}
    order_object = OrderModel(**order_mixed_data)
    try:
        session.start_transaction()
        updated_order = order_object.update_order(order_id, session)
        if order_object.state == "ready" and order["state"] != "ready":
            ProductModel.update_product_stock_by_name(order_object.items, session)
        session.commit_transaction()
        return db_json_response(updated_order)
    except Exception as e:
        session.abort_transaction()
        raise e
    finally:
        session.end_session()


@orders_route.route("/<order_id>", methods=["GET", "DELETE"])
@jwt_required()
def handle_order(order_id):
    token_data = get_jwt()
    token_id = token_data.get("sub")
    token_role = token_data.get("role")
    if request.method == "GET":
        order = OrderModel.get_order(order_id)
        if not order:
            raise ValueCustomError("not_found", orders_resource)
        user_order = order.get("user_id")
        if not any([token_id == user_order, token_role <= 1]):
            raise ValueCustomError("not_authorized")
        return db_json_response(order)

    if request.method == "DELETE":
        if not token_role <= 1:
            raise ValueCustomError("not_authorized")
        deleted_order = OrderModel.delete_order(order_id)
        if not deleted_order.deleted_count > 0:
            raise ValueCustomError("not_found", orders_resource)
        return success_json_response(order_id, orders_resource, "eliminado")
