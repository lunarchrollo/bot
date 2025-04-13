from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    country = Column(String)
    balance = Column(Float, default=0.0)
    referrer_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=True)
    wallet = Column(JSON, default={})
    tasks_done = Column(JSON, default=[])
    referral_earnings = Column(Float, default=0.0)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(Text)

engine = create_engine('sqlite:///bot.db')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
