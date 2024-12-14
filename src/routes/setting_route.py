from bson import ObjectId
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from pymongo import errors, ReturnDocument

from src.models.product_model import reload_allowed_values
from src.models.setting_model import SettingModel
from src.services.db_services import db
from src.utils.exceptions_management import (
    handle_unexpected_error,
    handle_validation_error,
    handle_duplicate_key_error,
    ClientCustomError,
)
from src.utils.successfully_responses import resource_msg, db_json_response

coll_settings = db.settings
setting_resource = "configuración"

setting_route = Blueprint("setting", __name__)


@setting_route.route("/setting", methods=["POST"])
@jwt_required()
def add_setting():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            setting_data = request.get_json()
            setting_object = SettingModel(**setting_data)
            new_setting = coll_settings.insert_one(setting_object.to_dict())
            return resource_msg(new_setting.inserted_id, setting_resource, "añadida", 201)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@setting_route.route("/settings", methods=["GET"])
@jwt_required()
def get_settings():
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        else:
            settings = coll_settings.find()
            return db_json_response(settings)
    except ClientCustomError as e:
        return e.response
    except Exception as e:
        return handle_unexpected_error(e)


@setting_route.route("/setting/<setting_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def manage_setting(setting_id):
    try:
        token_role = get_jwt().get("role")
        if token_role != 1:
            raise ClientCustomError("not_authorized")
        if request.method == "GET":
            setting = coll_settings.find_one({"_id": ObjectId(setting_id)})
            if setting:
                return db_json_response(setting)
            else:
                raise ClientCustomError("not_found", setting_resource)

        # TODO: Comprobar como podría hacer PATCH para poder optimizar el rendimiento de la base de datos
        if request.method == "PUT":
            setting = coll_settings.find_one({"_id": ObjectId(setting_id)}, {"_id": 0})
            if setting:
                data = request.get_json()
                mixed_data = {**setting, **data}
                setting_object = SettingModel(**mixed_data)
                updated_setting = coll_settings.find_one_and_update(
                    {"_id": ObjectId(setting_id)},
                    {"$set": setting_object.to_dict()},
                    return_document=ReturnDocument.AFTER,
                )
                reload_allowed_values()
                return db_json_response(updated_setting)
            else:
                raise ClientCustomError("not_found", setting_resource)

        if request.method == "DELETE":
            deleted_setting = coll_settings.delete_one({"_id": ObjectId(setting_id)})
            if deleted_setting.deleted_count > 0:
                return resource_msg(setting_id, setting_resource, "eliminada")
            else:
                raise ClientCustomError("not_found", setting_resource)
    except ClientCustomError as e:
        return e.response
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)
