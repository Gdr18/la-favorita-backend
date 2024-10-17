from flask import Blueprint, request
from bson import ObjectId
from pymongo import ReturnDocument, errors
from pydantic import ValidationError
from flask_jwt_extended import jwt_required

from ..utils.db_utils import db
from ..utils.exceptions_management import ClientCustomError, handle_validation_error, handle_unexpected_error, handle_duplicate_key_error
from ..utils.successfully_responses import resource_added_msg, resource_deleted_msg, db_json_response
from ..models.product_model import ProductModel

coll_products = db.products
product_resource = "producto"

product_route = Blueprint("product", __name__)


@product_route.route("/product", methods=["POST"])
@jwt_required()
def add_product():
    try:
        product_data = request.get_json()
        product_object = ProductModel(**product_data)
        new_product = coll_products.insert_one(product_object.to_dict())
        return resource_added_msg(new_product.inserted_id, product_resource)
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@product_route.route("/products", methods=["GET"])
@jwt_required()
def get_products():
    try:
        products = coll_products.find()
        return db_json_response(products)
    except Exception as e:
        return handle_unexpected_error(e)


@product_route.route("/product/<product_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def manage_product(product_id):
    if request.method == "GET":
        try:
            product = coll_products.find_one({"_id": ObjectId(product_id)})
            if product:
                return db_json_response(product)
            else:
                raise ClientCustomError(product_resource, product_id)
        except ClientCustomError as e:
            return e.json_response_not_found()
        except Exception as e:
            return handle_unexpected_error(e)

    if request.method == "PUT":
        try:
            product = coll_products.find_one({"_id": ObjectId(product_id)}, {"_id": 0})
            if product:
                data = request.get_json()
                combined_data = {**product, **data}
                product_object = ProductModel(**combined_data)
                # TODO: Cambiar la consulta por update_one para mejorar la consulta
                updated_product = coll_products.find_one_and_update(
                    {"_id": ObjectId(product_id)},
                    {"$set": product_object.to_dict()},
                    return_document=ReturnDocument.AFTER,
                )
                return db_json_response(updated_product)
            else:
                raise ClientCustomError(product_resource, product_id)
        except ClientCustomError as e:
            return e.json_response_not_found()
        except errors.DuplicateKeyError as e:
            return handle_duplicate_key_error(e)
        except ValidationError as e:
            return handle_validation_error(e)
        except Exception as e:
            return handle_unexpected_error(e)

    if request.method == "DELETE":
        try:
            deleted_product = coll_products.delete_one({"_id": ObjectId(product_id)})
            if deleted_product.deleted_count > 0:
                return resource_deleted_msg(product_id, product_resource)
            else:
                raise ClientCustomError(product_resource, product_id)
        except ClientCustomError as e:
            return e.json_response_not_found()
        except Exception as e:
            return handle_unexpected_error(e)
