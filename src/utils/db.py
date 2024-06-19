from pymongo import MongoClient
from flask_bcrypt import Bcrypt

from config import database

def db_connection():
    try:
        client = MongoClient(database)
        db = client["test_la_favorita"]
    except ConnectionError:
        print("No se pudo conectar a la base de datos")
    return db

db = db_connection()
bcrypt = Bcrypt()
