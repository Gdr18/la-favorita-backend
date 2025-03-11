from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from src.models.product_model import ProductModel
from src.models.dish_model import DishModel
from src.utils.exception_handlers import ValueCustomError, handle_validation_error, handle_unexpected_error
from src.utils.mongodb_exception_handlers import handle_mongodb_exception
from src.utils.json_responses import success_json_response, db_json_response
from src.services.db_services import client

products_resource = "producto"

products_route = Blueprint("products", __name__)


@products_route.route("/", methods=["POST"])
@jwt_required()
def add_product() -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role <= 2:
            raise ValueCustomError("not_authorized")
        else:
            product_data = request.get_json()
            product_object = ProductModel(**product_data)
            new_product = product_object.insert_product()
            return success_json_response(new_product.inserted_id, products_resource, "añadido", 201)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@products_route.route("/", methods=["GET"])
@jwt_required()
def get_products() -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role <= 2:
            raise ValueCustomError("not_authorized")
        else:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per-page", 10))
            skip = (page - 1) * per_page
            products = ProductModel.get_products(skip, per_page)
            return db_json_response(products)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@products_route.route("/<product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    session = client.start_session()
    token_role = get_jwt().get("role")
    try:
        if not token_role <= 2:
            raise ValueCustomError("not_authorized")
        product = ProductModel.get_product(product_id)
        if not product:
            raise ValueCustomError("not_found", products_resource)
        data = request.get_json()
        combined_data = {**product, **data}
        product_object = ProductModel(**combined_data)
        session.start_transaction()
        updated_product = product_object.update_product(product_id)
        updated_product_stock = updated_product.get("stock")
        product_stock = product.get("stock")
        if product_stock != updated_product_stock and 0 in (updated_product_stock, product_stock):
            DishModel.update_dishes_availability(updated_product.get("name"), updated_product_stock != 0)
        session.commit_transaction()
        return db_json_response(updated_product)
    except ValueCustomError as e:
        return e.response
    except ValidationError as e:
        return handle_validation_error(e)
    except PyMongoError as e:
        session.abort_transaction()
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)
    finally:
        session.end_session()


@products_route.route("/<product_id>", methods=["GET", "DELETE"])
@jwt_required()
def handle_product(product_id: str) -> tuple[Response, int]:
    try:
        token_role = get_jwt().get("role")
        if not token_role <= 2:
            raise ValueCustomError("not_authorized")
        if request.method == "GET":
            product = ProductModel.get_product(product_id)
            if product:
                return db_json_response(product)
            else:
                raise ValueCustomError("not_found", products_resource)

        if request.method == "DELETE":
            deleted_product = ProductModel.delete_product(product_id)
            if deleted_product.deleted_count > 0:
                return success_json_response(product_id, products_resource, "eliminado")
            else:
                raise ValueCustomError("not_found", products_resource)
    except ValueCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)
