from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime
from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Udhaar Ledger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CustomerCreate(BaseModel):
    name: str
    phone: str

class TransactionCreate(BaseModel):
    customer_id: int
    amount: float
    type: str

class CustomerRead(BaseModel):
    id: int
    name: str
    phone: str

    model_config = ConfigDict(from_attributes=True)

class TransactionRead(BaseModel):
    id: int
    customer_id: int
    amount: float
    type: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class LedgerRead(BaseModel):
    transactions: List[TransactionRead]
    balance: float

@app.post("/customers/", response_model=CustomerRead)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    name = customer.name.strip()
    phone = customer.phone.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required.")

    db_customer = models.Customer(name=name, phone=phone)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/customers/", response_model=List[CustomerRead])
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).order_by(models.Customer.id).all()

@app.post("/transaction/", response_model=TransactionRead)
def add_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == transaction.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive.")
    if transaction.type not in {"credit", "payment"}:
        raise HTTPException(status_code=400, detail="Type must be credit or payment.")

    db_txn = models.Transaction(
        customer_id=transaction.customer_id,
        amount=transaction.amount,
        type=transaction.type,
    )
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn

@app.get("/ledger/{customer_id}", response_model=LedgerRead)
def get_ledger(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.customer_id == customer_id)
        .order_by(models.Transaction.timestamp)
        .all()
    )
    balance = sum(t.amount if t.type == "credit" else -t.amount for t in txns)
    return {"transactions": txns, "balance": balance}
