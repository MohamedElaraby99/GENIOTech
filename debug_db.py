#!/usr/bin/env python3
"""
Debug script to check SQLite database setup
"""
import os
import sqlite3
from pathlib import Path

from app import app, db, Customer, User
from datetime import datetime

def check_customers():
    with app.app_context():
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(is_active=True).count()
        print(f"Total customers: {total_customers}")
        print(f"Active customers: {active_customers}")
        
        # Print first 5 active customers
        print("\nFirst 5 active customers:")
        active_customers = Customer.query.filter_by(is_active=True).limit(5).all()
        for customer in active_customers:
            print(f"- {customer.first_name} {customer.last_name} (ID: {customer.id})")

def create_test_customers():
    with app.app_context():
        # Get admin user for created_by_id
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Error: Admin user not found")
            return
        
        # Create test customers
        test_customers = [
            {"first_name": "John", "last_name": "Doe"},
            {"first_name": "Jane", "last_name": "Smith"},
            {"first_name": "Michael", "last_name": "Johnson"},
            {"first_name": "Sarah", "last_name": "Williams"},
            {"first_name": "David", "last_name": "Brown"}
        ]
        
        for customer_data in test_customers:
            customer = Customer(
                first_name=customer_data["first_name"],
                last_name=customer_data["last_name"],
                created_by_id=admin.id,
                is_active=True,
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(customer)
        
        try:
            db.session.commit()
            print("Created test customers successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test customers: {e}")

if __name__ == '__main__':
    print("Before creating test customers:")
    check_customers()
    
    print("\nCreating test customers...")
    create_test_customers()
    
    print("\nAfter creating test customers:")
    check_customers() 