"""Seed sample customers and orders for demo."""

import random
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Customer, Order

SAMPLE_CUSTOMERS = [
    ("Priya Sharma", "priya@example.com", "+919876543210"),
    ("Rahul Verma", "rahul@example.com", "+919876543211"),
    ("Ananya Patel", "ananya@example.com", "+919876543212"),
    ("Vikram Singh", "vikram@example.com", "+919876543213"),
    ("Sneha Reddy", "sneha@example.com", "+919876543214"),
    ("Arjun Mehta", "arjun@example.com", "+919876543215"),
    ("Kavya Nair", "kavya@example.com", "+919876543216"),
    ("Rohan Gupta", "rohan@example.com", "+919876543217"),
    ("Isha Joshi", "isha@example.com", "+919876543218"),
    ("Dev Malhotra", "dev@example.com", "+919876543219"),
]


def seed():
    db = SessionLocal()
    try:
        if db.query(Customer).count() > 0:
            print("Database already seeded, skipping.")
            return

        customers = []
        for i, (name, email, phone) in enumerate(SAMPLE_CUSTOMERS):
            days_ago = random.randint(1, 180)
            customer = Customer(
                name=name,
                email=email,
                phone=phone,
                created_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db.add(customer)
            customers.append(customer)

        db.flush()

        for customer in customers:
            num_orders = random.randint(0, 5)
            for _ in range(num_orders):
                days_ago = random.randint(1, 60)
                order = Order(
                    customer_id=customer.id,
                    amount=round(random.uniform(200, 5000), 2),
                    status="completed",
                    created_at=datetime.utcnow() - timedelta(days=days_ago),
                )
                db.add(order)

        db.commit()
        print(f"Seeded {len(customers)} customers with orders.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
