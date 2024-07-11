from flask import Blueprint, request, jsonify
from bson import json_util, ObjectId
from pymongo import ReturnDocument, errors

from ..utils.db import db
from ..models.product_model import ProductModel

coll_products = db.products

product = Blueprint("product", __name__)


@product.route("/product", methods=["POST"])
def add_product():
    product_data = request.get_json()
    try:
        product = ProductModel(**product_data).__dict__
        new_product = coll_products.insert_one(product)
        return (
            jsonify(
                {
                    "msg": f"El producto {new_product.inserted_id} ha sido añadido de forma satisfactoria"
                }
            ),
            200,
        )
    except errors.DuplicateKeyError as e:
        return (
            jsonify(
                {"err": f"Error de clave duplicada en MongoDB: {e.details['keyValue']}"}
            ),
            500,
        )
    except TypeError as e:
        if str(e).startswith("Product.__init__"):
            msg = str(e)[str(e).index(":") + 2 :].replace("and", "y")
            return (
                jsonify(
                    {
                        "err": f"Error: Se ha olvidado: {msg}. Son requeridos: 'name', 'categories', 'allergens' y 'stock'"
                    }
                ),
                500,
            )
        else:
            return jsonify({"err": f"Error: {str(e)}"}), 500
    except ValueError as e:
        return jsonify({"err": f"Error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"err": f"Error: {str(e)}"}), 500


@product.route("/products", methods=["GET"])
def get_products():
    products = coll_products.find()
    response = json_util.dumps(products)
    return response, 200


@product.route("/product/<id>", methods=["GET", "PUT", "DELETE"])
def manage_product(id):
    if request.method == "GET":
        product = coll_products.find_one({"_id": ObjectId(id)})
        if product:
            response = json_util.dumps(product)
            return response, 200
        else:
            return jsonify({"err": f"Error: El producto {id} no ha sido encontrado"}), 404

    elif request.method == "PUT":
        product = coll_products.find_one({"_id": ObjectId(id)})
        if product:
            product_data = request.get_json()
            
            updated_product = coll_products.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": product_data},
                return_document=ReturnDocument.AFTER,
            )
            if updated_product:
                return jsonify({"msg": f"El producto {id} ha sido actualizado"}), 200
        else:
            return jsonify({"err": f"Error: El producto {id} no ha sido encontrado"}), 404

    elif request.method == "DELETE":
        deleted_product = coll_products.find_one_and_delete({"_id": ObjectId(id)})
        if deleted_product:
            return jsonify({"msg": f"El producto {id} ha sido eliminado"}), 200
        else:
            return jsonify({"err": f"Error: El producto {id} no ha sido encontrado"}), 404
