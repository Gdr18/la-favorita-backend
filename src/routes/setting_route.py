from flask import Blueprint, request
from bson import ObjectId
from pymongo import errors, ReturnDocument
from pydantic import ValidationError

from ..utils.db_utils import db
from ..utils.exceptions_management import handle_unexpected_error, handle_validation_error, handle_duplicate_key_error, ResourceNotFoundError
from ..utils.successfully_responses import resource_added_msg, resource_deleted_msg, db_json_response

from ..models.setting_model import SettingModel

coll_settings = db.settings
setting_resource = "configuración"

setting_route = Blueprint("setting", __name__)


@setting_route.route("/setting", methods=["POST"])
def add_setting():
    try:
        setting_data = request.get_json()
        setting_object = SettingModel(**setting_data)
        new_setting = coll_settings.insert_one(setting_object.to_dict())
        return resource_added_msg(new_setting.inserted_id, setting_resource)
    except errors.DuplicateKeyError as e:
        return handle_duplicate_key_error(e)
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        return handle_unexpected_error(e)


@setting_route.route("/settings", methods=['GET'])
def get_settings():
    try:
        settings = coll_settings.find()
        return db_json_response(settings)
    except Exception as e:
        return handle_unexpected_error(e)


@setting_route.route("/setting/<setting_id>", methods=["GET", "PUT", "DELETE"])
def manage_setting(setting_id):
    if request.method == "GET":
        try:
            setting = coll_settings.find_one({"_id": ObjectId(setting_id)})
            if setting:
                return db_json_response(setting)
            else:
                raise ResourceNotFoundError(setting_id, setting_resource)
        except ResourceNotFoundError as e:
            return e.json_response()
        except Exception as e:
            return handle_unexpected_error(e)

    # TODO: Introducir actualización para las configuraciones
    if request.method == "PUT":
        try:
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
                return db_json_response(updated_setting)
            else:
                raise ResourceNotFoundError(setting_id, setting_resource)
        except ResourceNotFoundError as e:
            return e.json_response()
        except errors.DuplicateKeyError as e:
            return handle_duplicate_key_error(e)
        except ValidationError as e:
            return handle_validation_error(e)
        except Exception as e:
            return handle_unexpected_error(e)

    if request.method == "DELETE":
        try:
            deleted_setting = coll_settings.delete_one({"_id": ObjectId(setting_id)})
            if deleted_setting.deleted_count > 0:
                return resource_deleted_msg(setting_id, setting_resource)
            else:
                raise ResourceNotFoundError(setting_id, setting_resource)
        except ResourceNotFoundError as e:
            return e.json_response()
        except Exception as e:
            return handle_unexpected_error(e)
