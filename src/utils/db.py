from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os


bcrypt = Bcrypt()

load_dotenv(".env")


def db_connection():
    try:
        client = MongoClient(os.getenv("MONGO_DB_URI"))
        db = client["test_la_favorita"]
    except ConnectionError:
        print("No se pudo conectar a la base de datos")
    return db


db = db_connection()
