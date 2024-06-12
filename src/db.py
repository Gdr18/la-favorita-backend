from pymongo import MongoClient

import os

client = MongoClient(os.getenv("MONGO_DB_URI"))


def db_connection():
    try:
        client = MongoClient(os.getenv("MONGO_DB_URI"))
        db = client["test_restaurant"]
    except ConnectionError:
        print("No se pudo conectar a la base de datos")
    return db
