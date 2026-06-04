import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()

class Config:
    """Configuration de l'application."""

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    @classmethod
    def db_url(cls):
        """Construit l'URL SQLAlchemy proprement avec URL.create."""
        return URL.create(
            drivername="mysql+pymysql",
            username=cls.DB_USER,
            password=cls.DB_PASSWORD,
            host=cls.DB_HOST,
            database=cls.DB_NAME,
            query={"charset": "utf8mb4"}
        )