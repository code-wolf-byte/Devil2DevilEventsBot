# cogs/repositories.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///holi_bot.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

###############################################################################
# Database Models
###############################################################################
class HoliRole(Base):
    __tablename__ = "holi_roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, index=True)
    role_id = Column(BigInteger)
    color_name = Column(String)

class SplashLog(Base):
    __tablename__ = "splash_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, index=True)
    splasher_id = Column(BigInteger)
    target_id = Column(BigInteger)
    color_name = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

###############################################################################
# Create tables (if they don't already exist)
###############################################################################
Base.metadata.create_all(engine)

###############################################################################
# Repository Functions
###############################################################################
def add_holi_role(guild_id: int, role_id: int, color_name: str):
    session = SessionLocal()
    try:
        record = HoliRole(guild_id=guild_id, role_id=role_id, color_name=color_name)
        session.add(record)
        session.commit()
    finally:
        session.close()

def get_holi_roles(guild_id: int):
    session = SessionLocal()
    try:
        return session.query(HoliRole).filter_by(guild_id=guild_id).all()
    finally:
        session.close()

def clear_holi_roles(guild_id: int):
    """Remove all Holi roles from DB for the given guild."""
    session = SessionLocal()
    try:
        session.query(HoliRole).filter_by(guild_id=guild_id).delete()
        session.commit()
    finally:
        session.close()

def log_splash(guild_id: int, splasher_id: int, target_id: int, color_name: str):
    """Record a splash action in DB."""
    session = SessionLocal()
    try:
        new_log = SplashLog(
            guild_id=guild_id,
            splasher_id=splasher_id,
            target_id=target_id,
            color_name=color_name
        )
        session.add(new_log)
        session.commit()
    finally:
        session.close()

def get_splash_logs(guild_id: int, limit: int = 10):
    """Retrieve the most recent splash logs for the given guild."""
    session = SessionLocal()
    try:
        return (
            session.query(SplashLog)
            .filter_by(guild_id=guild_id)
            .order_by(SplashLog.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
