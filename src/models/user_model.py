import re
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo, ConfigDict

from ..utils.db_utils import bcrypt


# Campos únicos: email. Está configurado en MongoDB Atlas.
class UserModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8, max_length=60)
    role: int = Field(default=3, ge=1, le=3)
    phone: Optional[str] = None
    addresses: Optional[List[Dict]] = None
    basket: Optional[List[Dict]] = None

    model_config = ConfigDict(extra='forbid')

    @field_validator('password')
    def __validate_password(cls, v) -> str:
        bcrypt_pattern = re.compile(r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$')
        if bcrypt_pattern.match(v):
            return v
        if (
            len(v) >= 8
            and re.search(r"[A-Z]", v)
            and re.search(r"[a-z]", v)
            and re.search(r"[0-9]", v)
            and re.search(r"[!@#$%^&*_-]", v)
        ):
            hashing_v = cls.hashing_password(v)
            return hashing_v
        raise ValueError("La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial (!@#$%^&*_-)")

    @staticmethod
    def hashing_password(password) -> str:
        return bcrypt.generate_password_hash(password).decode("utf-8")

    @field_validator('phone')
    def __validate_phone(cls, v):
        if v is None:
            return v
        phone_pattern = re.compile(r"^(?:\+34)?\d{9}$")
        if phone_pattern.match(v):
            return v
        raise ValueError("El teléfono debe tener el prefijo +34 y/o 9 dígitos, y debe ser tipo string.")

    @field_validator('addresses', 'basket', mode='before')
    def __validate_addresses_and_basket(cls, v, field: ValidationInfo):
        if v is None:
            return v
        if isinstance(v, list) and all(isinstance(i, dict) for i in v):
            return v
        raise ValueError(f"El campo '{field.field_name}' debe ser una lista de diccionarios o None.")

    def to_dict(self) -> dict:
        return self.model_dump()
