# TODO: Comprobar si funcionan las condicionales con isinstance.


class User:
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
        if isinstance(name, str):
            self.name = name
        if isinstance(email, str):
            self.email = email
        if isinstance(password, str):
            self.password = password
        if isinstance(role, int) and role in [1, 2, 3]:
            self.role = role
        if phone and isinstance(phone, str):
            self.phone = phone
        if addresses and isinstance(addresses, list):
            self.addresses = addresses
        if basket and isinstance(basket, list):
            self.basket = basket
        if orders and isinstance(orders, list):
            self.orders = orders
