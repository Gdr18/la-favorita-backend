from typing import Union

from flask import Response
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from pymongo.errors import PyMongoError

from config import DATABASE_URI
from src.utils.exception_handlers import handle_mongodb_exception


def get_client() -> MongoClient:
    return MongoClient(DATABASE_URI)


def db_connection() -> Union[Database, tuple[Response, int]]:
    try:
        cl = get_client()
        database = cl["test_la_favorita"]
        return database
    except PyMongoError as e:
        return handle_mongodb_exception(e)


# Instancias necesarias para la conexión a la base de datos, el cifrado de contraseñas y autenticación JWT
db = db_connection()
client = get_client()
