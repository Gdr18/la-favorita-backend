from typing import List

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo.results import InsertOneResult, DeleteResult

from src.services.db_services import db


# Campos únicos: name. Está configurado en MongoDB Atlas.
class SettingModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    values: List[str] = Field(..., min_length=1)

    @field_validator("values", mode="after")
    @classmethod
    def __validate_values(cls, v):
        if (len(item) > 0 for item in v):
            return v
        else:
            raise ValueError("La lista de strings del campo 'values' debe tener al menos un caracter en cada string.")

    # Solicitudes a la colección settings
    def insert_setting(self) -> InsertOneResult:
        new_setting = db.settings.insert_one(self.model_dump())
        return new_setting

    @staticmethod
    def get_settings(skip: int, per_page: int) -> List[dict]:
        settings = db.settings.find().skip(skip).limit(per_page)
        return list(settings)

    @staticmethod
    def get_setting(setting_id: str) -> dict:
        setting = db.settings.find_one({"_id": ObjectId(setting_id)})
        return setting

    def update_setting(self, setting_id: str) -> dict:
        updated_setting = db.settings.find_one_and_update(
            {"_id": ObjectId(setting_id)}, {"$set": self.model_dump()}, return_document=True
        )
        return updated_setting

    @staticmethod
    def delete_setting(setting_id: str) -> DeleteResult:
        deleted_setting = db.settings.delete_one({"_id": ObjectId(setting_id)})
        return deleted_setting
