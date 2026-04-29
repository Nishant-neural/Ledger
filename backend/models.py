from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer)
    amount = Column(Float)
    type = Column(String)  # "credit" or "payment"
    timestamp = Column(DateTime, default=datetime.utcnow)