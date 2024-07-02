# No salta error si el tipo de dato no coincide. Utilizar isinstance(argumento, tipo_de_dato). Pensar en interable con *args.

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
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        if phone:
            self.phone = phone
        if addresses:
            self.addresses = addresses
        if basket:
            self.basket = basket
        if orders:
            self.orders = orders
