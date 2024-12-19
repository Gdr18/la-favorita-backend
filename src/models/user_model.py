import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union

from bson import ObjectId
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo, model_validator
from pymongo import ReturnDocument
from pymongo.results import InsertOneResult, DeleteResult

from src.services.db_services import db
from src.services.security_service import bcrypt


# Campos únicos: email. Está configurado en MongoDB Atlas.
class UserModel(BaseModel, extra="forbid"):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: Union[str, None] = None
    auth_provider: str = Field(default="email")
    role: int = Field(default=3, ge=1, le=3)
    phone: Optional[str] = Field(None, pattern=r"^(?:\+34)?\d{9}$")
    addresses: Optional[List[Dict]] = None
    basket: Optional[List[Dict]] = None
    confirmed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Union[datetime, None] = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))

    @model_validator(mode="after")
    def validate_model(self) -> "UserModel":
        if self.auth_provider == "google":
            self.confirmed = True
        if self.confirmed:
            self.expires_at = None
        if self.auth_provider == "email":
            self.password = self.validate_password(self.password)
        return self

    @field_validator("email", mode="after")
    @classmethod
    def validate_email(cls, v) -> EmailStr:
        try:
            validate_email(v)
            return v
        except EmailNotValidError as e:
            raise ValueError(f"El campo 'email' no es válido: {str(e)}")

    @staticmethod
    def validate_password(password: str) -> str:
        if password is None:
            raise ValueError("El campo 'password' es obligatorio.")
        bcrypt_pattern = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
        if bcrypt_pattern.match(password):
            return password
        if (
            8 <= len(password) <= 60
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"[0-9]", password)
            and re.search(r"[!@#$%^&*_-]", password)
        ):
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            return hashed_password
        else:
            raise ValueError(
                "El campo 'password' debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-)"
            )

    @field_validator("addresses", "basket", mode="before")
    @classmethod
    def validate_addresses_and_basket(cls, v, field: ValidationInfo):
        if v is None:
            return v
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):
            return v
        else:
            raise ValueError(f"El campo '{field.field_name}' debe ser una lista de diccionarios o None.")

    # Solicitudes a la colección users
    def insert_user(self) -> InsertOneResult:
        user = db.users.insert_one(self.model_dump())
        return user

    def insert_or_update_user_by_email(self) -> dict:
        user = db.users.find_one_and_update(
            {"email": self.email}, {"$set": self.model_dump()}, upsert=True, return_document=ReturnDocument.AFTER
        )
        return user

    @staticmethod
    def get_users(skip: int, per_page: int) -> list[dict]:
        users = db.users.find().skip(skip).limit(per_page)
        return list(users)

    @staticmethod
    def get_user_by_user_id(user_id: str) -> dict:
        user = db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0})
        return user

    @staticmethod
    def get_user_by_user_id_with_id(user_id: str) -> dict:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        return user

    @staticmethod
    def get_user_by_email(email: str) -> dict:
        user = db.users.find_one({"email": email})
        return user

    def update_user(self, user_id: str) -> dict:
        updated_user = db.users.find_one_and_update(
            {"_id": ObjectId(user_id)}, {"$set": self.model_dump()}, return_document=ReturnDocument.AFTER
        )
        return updated_user

    @staticmethod
    def delete_user(user_id: str) -> DeleteResult:
        deleted_user = db.users.delete_one({"_id": ObjectId(user_id)})
        return deleted_user
