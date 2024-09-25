# from ..utils.db_utils import type_checking

allowed_allergens = (
    "cereal",
    "huevo",
    "crustáceo",
    "pescado",
    "cacahuete",
    "soja",
    "lácteo",
    "fruto de cáscara",
    "apio",
    "mostaza",
    "sésamo",
    "sulfito",
    "altramuz",
    "molusco",
)
allowed_category = (
    "snack",
    "dulce",
    "fruta",
    "verdura",
    "carne",
    "pescado",
    "lácteo",
    "pan",
    "pasta",
    "arroz",
    "legumbre",
    "huevo",
    "salsa",
    "condimento",
    "especia",
    "aceite",
    "vinagre",
    "bebida alcohólica",
    "bebida no alcohólica",
    "bebida con gas",
    "bebida sin gas",
    "bebida alcohólica fermentada",
    "bebida energética",
    "bebida isotónica",
    "limpieza",
    "otro",
)


class ProductModel:
    def __init__(
        self,
        name: str,
        categories: list,
        stock: int,
        brand: str = None,
        allergens: list = None,
        notes: str = None,
    ):

        if type_checking(name, str, True):
            self.name = name

        if type_checking(categories, list, True) and self._checking_in_list(
            categories, allowed_category
        ):
            self.categories = categories

        if type_checking(stock, int, True):
            self.stock = stock

        if type_checking(brand, str):
            self.brand = brand

        if type_checking(allergens, list) and self._checking_in_list(
            allergens, allowed_allergens
        ):
            self.allergens = allergens

        if type_checking(notes, str):
            self.notes = notes

    def _checking_in_list(self, value: list, allowed_values: list) -> bool:
        if all(item in allowed_values for item in value):
            return True
        else:
            raise ValueError(
                f"el valor '{value}' no es válido en ese campo. Los valores permitidos son: {allowed_values}"
            )
