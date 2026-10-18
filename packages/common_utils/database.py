import os
from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./voicefront.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StorefrontModel(Base):
    __tablename__ = "storefronts"

    id = Column(String, primary_key=True, index=True)
    shop_name = Column(String, index=True)
    category = Column(String, index=True)
    spec_json = Column(JSON)
    html_content = Column(Text)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
