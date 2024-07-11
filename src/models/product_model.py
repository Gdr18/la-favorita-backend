from ..utils.db import type_checking

allowed_allergens = ["cereal", "huevo", "crustáceo", "pescado", "cacahuete", "soja", "lácteo", "fruto de cáscara", "apio", "mostaza", "sésamo", "sulfito", "altramuz", "molusco"]
allowed_category = ["snack", "dulce", "fruta", "verdura", "carne", "pescado", "lácteo", "pan", "pasta", "arroz", "legumbre", "huevo", "salsa", "condimento", "especia", "aceite", "vinagre", "bebida alcohólica", "bebida no alcohólica", "bebida con gas", "bebida sin gas", "bebida alcohólica fermentada", "bebida energética", "bebida isotónica", "limpieza"]

class ProductModel:
    def __init__(self, name: str, categories: list, allergens: list, stock: int):
        
        if type_checking(name, str):
            self.name = name
        if type_checking(categories, list):
            if all(category in allowed_category for category in categories):
                self.categories = categories
            else:
                raise ValueError(f"Las categorías no son válidas. Estas son las categorías válidas: {allowed_category}")
        if type_checking(allergens, list):
            if all(allergen in allowed_allergens for allergen in allergens):
                self.allergens = allergens
            else:
                raise ValueError(f"Los alérgenos no son válidos. Estos son los alérgenos válidos: {allowed_allergens}")
        if type_checking(stock, int):
            self.stock = stock
