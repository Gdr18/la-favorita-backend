from datetime import datetime, timezone

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
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(...)

    @field_validator("expires_at", mode="before")
    @classmethod
    def check_exp(cls, v):
        try:
            if isinstance(v, str):
                v = datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)
            elif isinstance(v, int) and len(str(v)) == 10:
                v = datetime.utcfromtimestamp(v)
            if v < datetime.now(timezone.utc):
                raise ValueError
            else:
                return v

        except (ValueError, TypeError):
            raise ValueError(
                "El campo 'expires_at' debe ser de tipo unix timestamp o cadena en formato ISO, además de mayor que la fecha actual UTC"
            )

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

    def update_refresh_token(self, token_id):
        refresh_token_updated = db.refresh_tokens.find_one_and_update(
            {"_id": ObjectId(token_id)}, {"$set": self.to_dict()}, return_document=ReturnDocument.AFTER
        )
        return refresh_token_updated

    @staticmethod
    def delete_refresh_token(token_id):
        refresh_token_deleted = db.refresh_tokens.delete_one({"_id": ObjectId(token_id)})
        return refresh_token_deleted

    @staticmethod
    def delete_refresh_token_by_user_id(user_id):
        refresh_token_deleted = db.refresh_tokens.delete_one({"user_id": user_id})
        return refresh_token_deleted

    # Solicitudes email token
    def insert_email_token(self):
        new_email_token = db.email_tokens.insert_one(self.to_dict())
        return new_email_token

    @staticmethod
    def get_email_tokens():
        email_tokens = db.email_tokens.find()
        return email_tokens

    @staticmethod
    def get_email_tokens_by_user_id(user_id):
        email_tokens = db.email_tokens.find({"user_id": user_id})
        return list(email_tokens)

    @staticmethod
    def get_email_token(token_id):
        email_token = db.email_tokens.find_one({"_id": ObjectId(token_id)}, {"_id": 0})
        return email_token

    @staticmethod
    def get_email_token_by_user_id(user_id):
        email_token = db.email_tokens.find_one({"user_id": user_id})
        return email_token

    def update_email_token(self, token_id):
        email_token_updated = db.email_tokens.find_one_and_update(
            {"_id": ObjectId(token_id)}, {"$set": self.to_dict()}, return_document=ReturnDocument.AFTER
        )
        return email_token_updated

    @staticmethod
    def delete_email_token(token_id):
        email_token_deleted = db.email_tokens.delete_one({"_id": ObjectId(token_id)})
        return email_token_deleted

    def to_dict(self):
        return self.model_dump()
