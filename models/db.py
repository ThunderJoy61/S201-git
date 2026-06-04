from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

engine = create_engine(
    Config.db_url(),
    pool_recycle=3600,
    pool_pre_ping=True
)

Session = sessionmaker(bind=engine)