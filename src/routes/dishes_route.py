from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo.errors import PyMongoError

from src.models.dish_model import DishModel
from src.utils.json_responses import success_json_response, db_json_response
from src.utils.exception_handlers import ClientCustomError, handle_unexpected_error, handle_validation_error
from src.utils.mongodb_exception_handlers import handle_mongodb_exception

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
        return success_json_response(new_dish.inserted_id, dishes_resource, "añadido")
    except ClientCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/")
def get_dishes():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per-page", 10))
        skip = (page - 1) * per_page
        dishes = DishModel.get_dishes(skip, per_page)
        return db_json_response(dishes)
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/category/<category>")
def get_category_dishes(category):
    try:
        dishes_by_category = DishModel.get_dishes_by_category(category)
        return db_json_response(dishes_by_category)
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except Exception as e:
        return handle_unexpected_error(e)


@dishes_route.route("/<dish_id>")
def get_dish(dish_id):
    try:
        dish = DishModel.get_dish(dish_id)
        if not dish:
            raise ClientCustomError("not_found", dishes_resource)
        return db_json_response(dish)
    except ClientCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
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
            dish = DishModel.get_dish(dish_id)
            if not dish:
                raise ClientCustomError("not_found", dishes_resource)
            dish_data = request.get_json()
            mixed_data = {**dish, **dish_data}
            dish_object = DishModel(**mixed_data)
            updated_dish = dish_object.update_dish(dish_id)
            return db_json_response(updated_dish)
        if request.method == "DELETE":
            deleted_dish = DishModel.delete_dish(dish_id)
            if not deleted_dish.deleted_count > 0:
                raise ClientCustomError("not_found", dishes_resource)
            return success_json_response(dish_id, dishes_resource, "eliminado")
    except ClientCustomError as e:
        return e.response
    except PyMongoError as e:
        return handle_mongodb_exception(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
