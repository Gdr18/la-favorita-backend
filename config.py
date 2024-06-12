from dotenv import load_dotenv
import os

load_dotenv(".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


config = os.getenv("MODE")
