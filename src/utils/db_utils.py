from pymongo.mongo_client import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from flask_bcrypt import Bcrypt

from config import database_uri


def db_connection() -> Database:
    try:
        client = MongoClient(database_uri)
        database = client["test_la_favorita"]
        return database
    except ConnectionFailure:
        print("No se pudo conectar a la base de datos")


# Instancias necesarias para la conexión a la base de datos y para el cifrado de contraseñas
db = db_connection()
bcrypt = Bcrypt()


# def get_allowed_values(collection_name):
#     collection = db[collection_name]
#     return [item["value"] for item in collection.find()]
#
#
# allowed_allergens = get_allowed_values("allergens")
# allowed_category = get_allowed_values("categories")
#
#
# def reload_allowed_values():
#     global allowed_allergens, allowed_category
#     allowed_allergens = get_allowed_values("allergens")
#     allowed_category = get_allowed_values("categories")
