from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create customer
@app.post("/customers/")
def create_customer(name: str, phone: str, db: Session = Depends(get_db)):
    customer = models.Customer(name=name, phone=phone)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

# Add transaction
@app.post("/transaction/")
def add_transaction(customer_id: int, amount: float, type: str, db: Session = Depends(get_db)):
    txn = models.Transaction(customer_id=customer_id, amount=amount, type=type)
    db.add(txn)
    db.commit()
    return {"message": "Transaction added"}

# Get ledger
@app.get("/ledger/{customer_id}")
def get_ledger(customer_id: int, db: Session = Depends(get_db)):
    txns = db.query(models.Transaction).filter(models.Transaction.customer_id == customer_id).all()

    balance = 0
    for t in txns:
        if t.type == "credit":
            balance += t.amount
        else:
            balance -= t.amount

    return {"transactions": txns, "balance": balance}