from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId
from pymongo import ReturnDocument, errors

from ..utils.db_utils import (
    db,
    unexpected_keyword_argument,
    required_positional_argument,
)
from ..models.product_model import ProductModel

coll_products = db.products

product = Blueprint("product", __name__)


@product.route("/product", methods=["POST"])
def add_product():
    try:
        product_data = request.get_json()
        product = ProductModel(**product_data).__dict__
        new_product = coll_products.insert_one(product)
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
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            return unexpected_keyword_argument(e)
        elif "required positional argument" in str(e):
            return required_positional_argument(e, "name", "categories", "stock")
        else:
            return jsonify({"err": f"Error: {e}"}), 400
    except ValueError as e:
        return jsonify({"err": f"Error: {e}"}), 400
    except Exception as e:
        return (
            jsonify(err=f"Error: Ha ocurrido un error inesperado. {e}"),
            500,
        )


@product.route("/products", methods=["GET"])
def get_products():
    try:
        products = coll_products.find()
        response = json_util.dumps(products)
        return response, 200
    except Exception as e:
        return jsonify(err=f"Error: Ha ocurrido un error inesperado. {e}"), 500


@product.route("/product/<product_id>", methods=["GET", "PUT", "DELETE"])
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
                        err=f"Error: El producto {product_id} no ha sido encontrado"
                    ),
                    404,
                )
        except Exception as e:
            return (
                jsonify(err=f"Error: Ha ocurrido un error inesperado. {e}"),
                500,
            )

    elif request.method == "PUT":
        try:
            product = coll_products.find_one({"_id": ObjectId(product_id)}, {"_id": 0})
            if product:
                product.update(request.get_json())
                product_data = ProductModel(**product).__dict__
                # TODO: Cambiar la consulta por update_one para mejorar la consulta
                updated_product = coll_products.find_one_and_update(
                    {"_id": ObjectId(product_id)},
                    {"$set": product_data},
                    return_document=ReturnDocument.AFTER,
                )
                response = json_util.dumps(updated_product)
                return response
            else:
                return (
                    jsonify(
                        err=f"Error: El producto {product_id} no ha sido encontrado"
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
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                return unexpected_keyword_argument(e)
            else:
                return jsonify(err=f"Error: {e}"), 400
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
                        err=f"Error: El producto {product_id} no ha sido encontrado"
                    ),
                    404,
                )
        except Exception as e:
            return (
                jsonify(err=f"Error: Ha ocurrido un error inesperado. {e}"),
                500,
            )
