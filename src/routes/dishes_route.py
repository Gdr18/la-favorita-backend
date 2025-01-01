from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from src.models.dish_model import DishModel
from src.utils.successfully_responses import resource_msg, db_json_response
from src.utils.exceptions_management import (
    ClientCustomError,
    handle_unexpected_error,
    handle_validation_error,
    handle_duplicate_key_error,
)

dishes_resource = "plato"

dishes_route = Blueprint("dishes", __name__)


@dishes_route.route("/", methods=["POST"])
@jwt_required()
def insert_dish():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        dish_data = request.get_json()
        dish_object = DishModel(**dish_data)
        new_dish = dish_object.insert_dish()
        return resource_msg(new_dish.inserted_id, dishes_resource, "añadido")
    except ClientCustomError as e:
        return e.response
    except DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/")
def get_dishes():
    try:
        page = request.args.get("page", 1)
        per_page = request.args.get("per-page", 10)
        skip = (page - 1) * per_page
        dishes = DishModel.get_dishes(per_page, skip)
        return db_json_response(dishes)
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/category/<category>")
def get_category_dishes(category):
    try:
        dishes_by_category = DishModel.get_dishes_by_category(category)
        return db_json_response(dishes_by_category)
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/<dish_id>")
def get_dish(dish_id):
    try:
        dish = DishModel.get_dish(dish_id)
        if not dish:
            raise ClientCustomError("not_found", dishes_resource)
        response = db_json_response(dish)
        print("hola")
        return response
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/<dish_id>", methods=["PUT", "DELETE"])
@jwt_required()
def handle_dish(dish_id):
    token_role = get_jwt().get("role")
    try:
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        if request.method == "PUT":
            dish_data = request.get_json()
            dish = DishModel.get_dish(dish_id)
            print(dish)
            if not dish:
                raise ClientCustomError("not_found", dishes_resource)
            mixed_data = {**dish, **dish_data}
            updated_dish = DishModel.update_dish(dish_id, mixed_data)
            return db_json_response(updated_dish)
        if request.method == "DELETE":
            deleted_dish = DishModel.delete_dish(dish_id)
            if not deleted_dish.deleted_count > 0:
                raise ClientCustomError("not_found", dishes_resource)
            return resource_msg(dish_id, dishes_resource, "eliminado")
    except ClientCustomError as e:
        return e.response
    except DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
