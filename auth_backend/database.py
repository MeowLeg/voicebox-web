from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, Float, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    audio_records = relationship("AudioRecord", back_populates="user", cascade="all, delete-orphan")


class AudioRecord(Base):
    __tablename__ = "audio_records"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    voicebox_generation_id = Column(String, nullable=True, index=True)
    profile_id = Column(String, nullable=True)
    profile_name = Column(String, nullable=True)
    text = Column(String, nullable=False)
    language = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    seed = Column(Integer, nullable=True)
    instruct = Column(String, nullable=True)
    engine = Column(String, nullable=True)
    model_size = Column(String, nullable=True)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audio_records")


class QueueTask(Base):
    __tablename__ = "queue_tasks"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    request_data = Column(JSON, nullable=False)
    voicebox_generation_id = Column(String, nullable=True, index=True)
    status = Column(String, default="pending", index=True)
    position = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    error = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
