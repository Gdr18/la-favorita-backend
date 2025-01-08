from flask import request, Blueprint, Response
from flask_jwt_extended import get_jwt, jwt_required
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from src.models.order_model import OrderModel
from src.models.product_model import ProductModel
from src.utils.successfully_responses import resource_msg, db_json_response
from src.utils.exceptions_management import ClientCustomError, handle_unexpected_error, handle_validation_error
from src.services.db_services import client

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
    # except ValidationError as e:
    #     return handle_validation_error(e)
    except ValidationError as e:
        print(e.errors())
        return handle_unexpected_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@orders_route.route("/")
@jwt_required()
def get_orders() -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role <= 1:
            raise ClientCustomError("not_authorized")
        page = request.args.get("page", 1)
        per_page = request.args.get("per-page", 10)
        skip = (page - 1) * per_page
        orders = OrderModel.get_orders(skip, per_page)
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
        if not any([token_id == user_id, token_role <= 1]):
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


@orders_route.route("/<order_id>", methods=["PUT"])
@jwt_required()
def update_order(order_id):
    session = client.start_session()
    try:
        token_id = get_jwt().get("sub")
        token_role = get_jwt().get("role")
        order = OrderModel.get_order(order_id)
        if not order:
            raise ClientCustomError("not_found", orders_resource)
        user_order = order.get("user_id")
        if not any([token_id == user_order, token_role <= 1]):
            raise ClientCustomError("not_authorized")
        order_new_data = request.get_json()
        if order_new_data.get("state") and order["state"] != order_new_data.get("state"):
            OrderModel.check_level_state(order_new_data.get("state"), order["state"])
        order_mixed_data = {**order, **order_new_data}
        order_object = OrderModel(**order_mixed_data)
        session.start_transaction()
        updated_order = order_object.update_order(order_id)
        if order_object.state == "ready":
            ProductModel.update_product_stock_by_name(order_object.items)
        session.commit_transaction()
        return db_json_response(updated_order)
    except ClientCustomError as e:
        return e.response
    except ValidationError as e:
        return handle_validation_error(e)
    except PyMongoError as e:
        session.abort_transaction()
        return handle_unexpected_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
    finally:
        session.end_session()


@orders_route.route("/<order_id>", methods=["GET", "DELETE"])
@jwt_required()
def handle_order(order_id):
    try:
        token_id = get_jwt().get("sub")
        token_role = get_jwt().get("role")
        if request.method == "GET":
            order = OrderModel.get_order(order_id)
            user_order = order.get("user_id")
            if not any([token_id == user_order, token_role <= 1]):
                raise ClientCustomError("not_authorized")
            return db_json_response(order)

        if request.method == "DELETE":
            if not token_role <= 1:
                raise ClientCustomError("not_authorized")
            deleted_order = OrderModel.delete_order(order_id)
            if not deleted_order.deleted_count > 0:
                raise ClientCustomError("not_found", orders_resource)
            return resource_msg(order_id, orders_resource, "eliminado")

    except ClientCustomError as e:
        return e.response
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
