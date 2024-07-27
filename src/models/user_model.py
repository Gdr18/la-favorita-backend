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
        if type_checking(name, str, True):
            self.name = name

        if type_checking(email, str, True) and self._validate_email(email):
            self.email = email

        # TODO: Incluir la función de validación de contraseña
        if type_checking(password, str, True):
            self.password = password

        if type_checking(role, int, True) and self._validate_role(role):
            self.role = role

        if type_checking(phone, str):
            self.phone = phone

        if type_checking(addresses, list):
            self.addresses = addresses

        if type_checking(basket, list):
            self.basket = basket

        if type_checking(orders, list):
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

    def _validate_password(self) -> bool:
        if (
            len(self.password) >= 8
            and re.search(r"[A-Z]", self.password)
            and re.search(r"[a-z]", self.password)
            and re.search(r"[0-9]", self.password)
            and re.search(r"[!@#$%^&*_-]", self.password)
        ):
            return True
        else:
            raise ValueError("La contraseña debe tener al menos 8 caracteres, contener al menos una mayúscula, una minúscula, un número y un carácter especial")
        
    # TODO: Comprobar si se puede mejorar
    def _hashing_password(self):
        self.password = bcrypt.generate_password_hash(self.password).decode("utf-8")
        return self.password

