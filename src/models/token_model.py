from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo import ReturnDocument

from ..utils.db_utils import db


# Campo único: "jti" y "user_id", configurado en MongoDB Atlas.
# Campo TTL: "expires_at", configurado en MongoDB Atlas. El documento se eliminará automáticamente cuando expire la fecha.
# TODO: Probar si funciona datetime.
class TokenModel(BaseModel, extra="forbid"):
    user_id: str = Field(..., pattern=r"^[a-f0-9]{24}$")
    jti: str = Field(..., pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)

    @field_validator("expires_at", mode="before")
    @classmethod
    def check_exp(cls, v):
        if isinstance(v, int) and len(str(v)) == 10 and v > datetime.utcnow().timestamp():
            return datetime.utcfromtimestamp(v)
        raise ValueError("El campo 'expires_at' debe ser de tipo unix timestamp y mayor que la fecha actual")

    # Solicitudes refresh token
    def insert_refresh_token(self):
        new_refresh_token = db.refresh_tokens.insert_one(self.to_dict())
        return new_refresh_token

    @staticmethod
    def get_refresh_tokens():
        refresh_tokens = db.refresh_tokens.find()
        return refresh_tokens

    @staticmethod
    def get_refresh_token(token_id):
        # TODO: Cuando se implemente el front mirar si hace falta el "_id": 0
        refresh_token = db.refresh_tokens.find_one({"_id": ObjectId(token_id)}, {"_id": 0})
        return refresh_token

    def update_refresh_token(self):
        updated_refresh_token = db.refresh_tokens.find_one_and_update(
            {"_id": ObjectId(self.user_id)}, {"$set": self.to_dict()}, return_document=ReturnDocument.AFTER
        )
        return updated_refresh_token

    @staticmethod
    def delete_refresh_token(token_id):
        deleted_refresh_token = db.refresh_tokens.delete_one({"_id": ObjectId(token_id)})
        return deleted_refresh_token

    def to_dict(self):
        return self.model_dump()
