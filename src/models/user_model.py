import re

from ..utils.db_utils import type_checking


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

        if self._validate_email and type_checking(email, str):
            self.email = email

        # TODO: Implementar validación de contraseña según los criterios deseados
        if type_checking(password, str):
            self.password = password

        if type_checking(role, int) and role in [1, 2, 3]:
            self.role = role
        else:
            raise ValueError("'role' debe tener el valor 1, 2 o 3")

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
