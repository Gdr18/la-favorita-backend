import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union

from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from pymongo import ReturnDocument

from src.services.db_services import db
from src.services.security_service import bcrypt


# Campos únicos: email. Está configurado en MongoDB Atlas.
class UserModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: Optional[str] = None
    auth_provider: str = Field(default="email")
    role: int = Field(default=3, ge=1, le=3)
    phone: Optional[str] = Field(None, pattern=r"^(?:\+34)?\d{9}$")
    addresses: Optional[List[Dict]] = None
    basket: Optional[List[Dict]] = None
    confirmed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Union[datetime, None] = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v) -> EmailStr:
        if v is None:
            raise ValueError("El campo 'email' es obligatorio.")
        try:
            validate_email(v)
            return v
        except EmailNotValidError as e:
            raise ValueError(f"El campo 'email' no es válido: {str(e)}")

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v, values: ValidationInfo) -> Union[str, None]:
        auth_provider = values.data.get("auth_provider")
        if v is None and auth_provider == "google":
            return v
        if v is None:
            raise ValueError("El campo 'password' es obligatorio.")
        bcrypt_pattern = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
        if bcrypt_pattern.match(v):
            return v
        if (
            8 <= len(v) <= 60
            and re.search(r"[A-Z]", v)
            and re.search(r"[a-z]", v)
            and re.search(r"[0-9]", v)
            and re.search(r"[!@#$%^&*_-]", v)
        ):
            hashing_v = cls.hashing_password(v)
            return hashing_v
        else:
            raise ValueError(
                "El campo 'password' debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-)"
            )

    @staticmethod
    def hashing_password(password) -> str:
        return bcrypt.generate_password_hash(password).decode("utf-8")

    @field_validator("addresses", "basket", mode="before")
    @classmethod
    def validate_addresses_and_basket(cls, v, field: ValidationInfo):
        if v is None:
            return v
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):
            return v
        else:
            raise ValueError(f"El campo '{field.field_name}' debe ser una lista de diccionarios o None.")

    @field_validator("expires_at", mode="before")
    @classmethod
    def validate_expires_at(cls, v, values: ValidationInfo) -> Union[datetime, None]:
        value_confirmed = values.data.get("confirmed")
        if value_confirmed:
            return None
        if isinstance(v, datetime):
            return v
        else:
            raise ValueError("El campo 'expires_at' debe ser de tipo datetime o None.")

    # Solicitudes a la colección users
    def insert_user(self):
        user = db.users.insert_one(self.model_dump())
        return user

    def insert_or_update_user_by_email(self):
        user = db.users.find_one_and_update(
            {"email": self.email}, {"$set": self.model_dump()}, upsert=True, return_document=ReturnDocument.AFTER
        )
        return user

    @staticmethod
    def get_users():
        users = db.users.find()
        return list(users)

    @staticmethod
    def get_user_by_user_id(user_id):
        user = db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
        return user

    @staticmethod
    def get_user_by_user_id_with_id(user_id):
        user = db.users.find_one({"_id": ObjectId(user_id)})
        return user

    @staticmethod
    def get_user_by_email(email):
        user = db.users.find_one({"email": email})
        return user

    def update_user(self, user_id):
        updated_user = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return updated_user

    @staticmethod
    def delete_user(user_id):
        db.users.delete_one({"_id": ObjectId(user_id)})
        return user_id
