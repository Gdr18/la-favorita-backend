import re
from pydantic import BaseModel, EmailStr, Field, field_validator
# from typing import List, Optional

from ..utils.db_utils import bcrypt


# TODO: Verificar que todo funciona correctamente
# Campos únicos: email. Está configurado en MongoDB Atlas.
# noinspection PyMethodParameters
class UserModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8, max_length=50)
    role: int = Field(default=3, ge=1, le=3)
    phone: str = None
    addresses: list = None
    basket: dict = None

    @field_validator('password')
    def validate_password(cls, v):
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
            return v
        else:
            raise ValueError("La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial")

    def hashing_password(self):
        self.password = bcrypt.generate_password_hash(self.password).decode("utf-8")

    @field_validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        phone_pattern = re.compile(r"^\+?34?\d{9}$")
        if phone_pattern.match(v):
            return v
        else:
            raise ValueError("El número de teléfono no es válido")
