from datetime import datetime, timezone
import re

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult, DeleteResult

from src.services.db_services import db


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
        re_date_iso8601_timezone = (
            r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):([0-5]\d):([0-5]\d)(\+[01]\d:[0-5]\d)$"
        )
        re_date_iso8601 = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
        if re.match(re_date_iso8601_timezone, v) or re.match(re_date_iso8601, v):
            v = datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)
        elif isinstance(v, int) and len(str(v)) == 10:
            v = datetime.fromtimestamp(v).astimezone(timezone.utc)
        else:
            raise ValueError(
                "El campo 'expires_at' debe ser una fecha de tipo unix timestamp o cadena en formato ISO 8601"
            )
        if v < datetime.now(timezone.utc):
            raise ValueError("El campo 'expires_at' debe ser mayor que la fecha actual UTC")
        return v

    # Solicitudes a la colección refresh_tokens
    def insert_refresh_token(self) -> InsertOneResult:
        new_refresh_token = db.refresh_tokens.insert_one(self.model_dump())
        return new_refresh_token

    @staticmethod
    def get_refresh_tokens(skip: int, per_page: int) -> list[dict]:
        refresh_tokens = db.refresh_tokens.find().skip(skip).limit(per_page)
        return list(refresh_tokens)

    @staticmethod
    def get_refresh_token_by_token_id(token_id: str) -> dict:
        refresh_token = db.refresh_tokens.find_one({"_id": ObjectId(token_id)}, {"_id": 0})
        return refresh_token

    @staticmethod
    def get_refresh_token_by_user_id(user_id: str) -> dict:
        refresh_token = db.refresh_tokens.find_one({"user_id": user_id})
        return refresh_token

    def update_refresh_token(self, token_id: str) -> dict:
        refresh_token_updated = db.refresh_tokens.find_one_and_update(
            {"_id": ObjectId(token_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return refresh_token_updated

    @staticmethod
    def delete_refresh_token_by_token_id(token_id: str) -> DeleteResult:
        refresh_token_deleted = db.refresh_tokens.delete_one({"_id": ObjectId(token_id)})
        return refresh_token_deleted

    @staticmethod
    def delete_refresh_token_by_user_id(user_id: str) -> DeleteResult:
        refresh_token_deleted = db.refresh_tokens.delete_one({"user_id": user_id})
        return refresh_token_deleted

    # Solicitudes a la colección email_tokens
    def insert_email_token(self) -> InsertOneResult:
        new_email_token = db.email_tokens.insert_one(self.model_dump())
        return new_email_token

    @staticmethod
    def get_email_tokens(skip: int, per_page: int) -> list[dict]:
        email_tokens = db.email_tokens.find().skip(skip).limit(per_page)
        return list(email_tokens)

    @staticmethod
    def get_email_tokens_by_user_id(user_id: str) -> list[dict]:
        email_tokens = db.email_tokens.find({"user_id": user_id})
        return list(email_tokens)

    @staticmethod
    def get_email_token_by_token_id(token_id: str) -> dict:
        email_token = db.email_tokens.find_one({"_id": ObjectId(token_id)}, {"_id": 0})
        return email_token

    @staticmethod
    def get_email_token_by_user_id(user_id: str) -> dict:
        email_token = db.email_tokens.find_one({"user_id": user_id})
        return email_token

    def update_email_token(self, token_id: str) -> dict:
        email_token_updated = db.email_tokens.find_one_and_update(
            {"_id": ObjectId(token_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return email_token_updated

    @staticmethod
    def delete_email_token(token_id: str) -> DeleteResult:
        email_token_deleted = db.email_tokens.delete_one({"_id": ObjectId(token_id)})
        return email_token_deleted

    # Solicitudes a la colección revoke_tokens

    def insert_revoked_token(self) -> InsertOneResult:
        new_revoke_token = db.revoked_tokens.insert_one(self.model_dump())
        return new_revoke_token

    @staticmethod
    def get_revoked_tokens(skip: int, per_page: int) -> list[dict]:
        revoke_tokens = db.revoked_tokens.find().skip(skip).limit(per_page)
        return list(revoke_tokens)

    @staticmethod
    def get_revoked_token_by_token_id(token_id: str) -> dict:
        revoke_token = db.revoked_tokens.find_one({"_id": ObjectId(token_id)}, {"_id": 0})
        return revoke_token

    @staticmethod
    def get_revoked_token_by_jti(jti: str) -> dict:
        revoke_token = db.revoked_tokens.find_one({"jti": jti})
        return revoke_token

    def update_revoked_token(self, token_id: str) -> dict:
        revoke_token_updated = db.revoked_tokens.find_one_and_update(
            {"_id": ObjectId(token_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return revoke_token_updated

    @staticmethod
    def delete_revoked_token(token_id: str) -> DeleteResult:
        revoke_token_deleted = db.revoked_tokens.delete_one({"_id": ObjectId(token_id)})
        return revoke_token_deleted
