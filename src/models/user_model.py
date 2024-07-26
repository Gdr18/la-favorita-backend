import re

from ..utils.db_utils import type_checking, bcrypt


class UserModel:
    def __init__(
        self,
        name: str,
        email: str,
        password: str,
        role: int = 3,
        phone: str = None,
        addresses: list = None,
        basket: list = None,
        orders: list = None,
    ):
        if type_checking(name, str):
            self.name = name

        if type_checking(email, str) and self._validate_email(email):
            self.email = email

        # TODO: Incluir la función de validación de contraseña
        if type_checking(password, str) and self._validate_password(password):
            self.password = password

        if type_checking(role, int) and self._validate_role(role):
            self.role = role

        if phone and type_checking(phone, str):
            self.phone = phone

        if addresses and type_checking(addresses, list):
            self.addresses = addresses

        if basket and type_checking(basket, list):
            self.basket = basket

        if orders and type_checking(orders, list):
            self.orders = orders

    def _validate_email(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if re.match(pattern, email):
            return True
        else:
            raise ValueError("El email no es válido")

    def _validate_role(self, role: int) -> bool:
        if role in (1, 2, 3):
            return True
        else:
            raise ValueError("'role' debe tener el valor 1, 2 o 3")

    def _validate_password(self, password: str) -> bool:
        if (
            len(password) >= 8
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"[0-9]", password)
            and re.search(r"[!@#$%^&*_-]", password)
        ):
            return True
        else:
            raise ValueError("La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial")
        
    def hashing_password(self):
        self.password = bcrypt.generate_password_hash(self.password).decode("utf-8")
        return self.password

