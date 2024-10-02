from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId
from pymongo import ReturnDocument, errors
from pydantic import ValidationError

from ..utils.db_utils import (
    db, extra_inputs_are_not_permitted, field_required, input_should_be, value_error_formatting
)
from ..models.product_model import ProductModel

coll_products = db.products

product_route = Blueprint("product", __name__)


@product_route.route("/product", methods=["POST"])
def add_product():
    try:
        product_data = request.get_json()
        product_object = ProductModel(**product_data)
        new_product = coll_products.insert_one(product_object.to_dict())
        return (
            jsonify(
                msg=f"El producto {new_product.inserted_id} ha sido añadido de forma satisfactoria"
            ),
            200,
        )
    except errors.DuplicateKeyError as e:
        return (
            jsonify(
                err=f"Error de clave duplicada en MongoDB: {e.details['keyValue']}"
            ),
            409,
        )
    except ValidationError as e:
        errors_list = e.errors()
        for error in errors_list:
            if error["msg"] == "Field required":
                return field_required(errors_list)
            if error["msg"].startswith("Input should be"):
                return input_should_be(errors_list)
            if error["msg"] == "Extra inputs are not permitted":
                return extra_inputs_are_not_permitted(errors_list)
            if error["msg"].startswith("Value error"):
                return value_error_formatting(errors_list)

        return jsonify(err=errors_list), 400
    except Exception as e:
        return (
            jsonify(err=f"Ha ocurrido un error inesperado. {e}"),
            500,
        )


@product_route.route("/products", methods=["GET"])
def get_products():
    try:
        products = coll_products.find()
        response = json_util.dumps(products)
        return response, 200
    except Exception as e:
        return jsonify(err=f"Ha ocurrido un error inesperado. {e}"), 500


@product_route.route("/product/<product_id>", methods=["GET", "PUT", "DELETE"])
def manage_product(product_id):
    if request.method == "GET":
        try:
            product = coll_products.find_one({"_id": ObjectId(product_id)})
            if product:
                response = json_util.dumps(product)
                return response, 200
            else:
                return (
                    jsonify(
                        err=f"El producto {product_id} no ha sido encontrado"
                    ),
                    404,
                )
        except Exception as e:
            return (
                jsonify(err=f"Ha ocurrido un error inesperado. {e}"),
                500,
            )

    elif request.method == "PUT":
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
                response = json_util.dumps(updated_product)
                return response
            else:
                return (
                    jsonify(
                        err=f"El producto {product_id} no ha sido encontrado"
                    ),
                    404,
                )
        except errors.DuplicateKeyError as e:
            return (
                jsonify(
                    err=f"Error de clave duplicada en MongoDB: {e.details['keyValue']}"
                ),
                409,
            )
        except ValidationError as e:
            errors_list = e.errors()
            for error in errors_list:
                if error["msg"] == "Field required":
                    return field_required(errors_list)
                if error["msg"].startswith("Input should be"):
                    return input_should_be(errors_list)
                if error["msg"] == "Extra inputs are not permitted":
                    return extra_inputs_are_not_permitted(errors_list)
                if error["msg"].startswith("Value error"):
                    return value_error_formatting(errors_list)

            return jsonify(err=errors_list), 400
        except Exception as e:
            return jsonify(err=f"Error: {e}"), 500

    elif request.method == "DELETE":
        try:
            deleted_product = coll_products.delete_one({"_id": ObjectId(product_id)})
            if deleted_product.deleted_count > 0:
                return (
                    jsonify(
                        msg=f"El producto {product_id} ha sido eliminado de forma satisfactoria"
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        err=f"El producto {product_id} no ha sido encontrado"
                    ),
                    404,
                )
        except Exception as e:
            return (
                jsonify(err=f"Ha ocurrido un error inesperado. {e}"),
                500,
            )
