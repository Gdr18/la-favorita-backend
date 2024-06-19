from dotenv import load_dotenv
import os

load_dotenv(".env")

database = os.getenv("MONGO_DB_URI")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


config = os.getenv("CONFIG")
