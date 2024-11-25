import os

from dotenv import load_dotenv

load_dotenv(".env")

database_uri = os.getenv("MONGO_DB_URI")
google_client_id = os.getenv("CLIENT_ID")
google_client_secret = os.getenv("CLIENT_SECRET")


class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 900
    SECRET_KEY = os.getenv("SECRET_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


config = os.getenv("CONFIG")
