#!/usr/bin/env python3
"""
Debug script to check SQLite database setup
"""
import os
import sqlite3
from pathlib import Path

from app import db, User, Customer, Course, Ticket, Session, Note, CourseCategory, Group, GroupSchedule
from app import GroupMember, GroupSession, GroupAttendance, AuditLog, CustomerHistory, GroupHistory, Performance, Communication
from app import app  # Import the Flask app

print("🔍 Debug: SQLite Database Setup")
print("="*50)

# Get current directory
current_dir = os.getcwd()
print(f"Current directory: {current_dir}")

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Script directory: {script_dir}")

# Check instance directory
instance_dir = os.path.join(script_dir, "instance")
print(f"Instance directory: {instance_dir}")
print(f"Instance exists: {os.path.exists(instance_dir)}")

if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
    print("✅ Created instance directory")

# Database file path
db_path = os.path.join(instance_dir, "crm.db")
print(f"Database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

# Check permissions
try:
    # Try to create/open the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test creating a simple table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    
    # Test inserting data
    cursor.execute("INSERT INTO test (name) VALUES (?)", ("test_entry",))
    conn.commit()
    
    # Test querying
    cursor.execute("SELECT * FROM test")
    result = cursor.fetchall()
    print(f"✅ Database test successful: {result}")
    
    # Clean up test table
    cursor.execute("DROP TABLE test")
    conn.commit()
    conn.close()
    
    print("✅ SQLite database is working correctly!")
    
except Exception as e:
    print(f"❌ Database error: {e}")

# Test the SQLAlchemy URL format
base_dir = os.path.abspath(os.path.dirname(__file__))
db_url = f'sqlite:///{os.path.join(base_dir, "instance", "crm.db")}'
print(f"SQLAlchemy URL: {db_url}")

# Test loading the app config
try:
    from config import config
    app_config = config['development']
    print(f"App config DB URI: {app_config.SQLALCHEMY_DATABASE_URI}")
except Exception as e:
    print(f"❌ Config error: {e}") 

def clear_database():
    """Clear all data from the database while respecting foreign key constraints."""
    print("Starting database cleanup...")
    
    try:
        # Delete data in reverse order of dependencies
        print("Deleting Communication records...")
        Communication.query.delete()
        
        print("Deleting Performance records...")
        Performance.query.delete()
        
        print("Deleting GroupHistory records...")
        GroupHistory.query.delete()
        
        print("Deleting CustomerHistory records...")
        CustomerHistory.query.delete()
        
        print("Deleting AuditLog records...")
        AuditLog.query.delete()
        
        print("Deleting GroupAttendance records...")
        GroupAttendance.query.delete()
        
        print("Deleting GroupSession records...")
        GroupSession.query.delete()
        
        print("Deleting GroupMember records...")
        GroupMember.query.delete()
        
        print("Deleting GroupSchedule records...")
        GroupSchedule.query.delete()
        
        print("Deleting Group records...")
        Group.query.delete()
        
        print("Deleting CourseCategory records...")
        CourseCategory.query.delete()
        
        print("Deleting Note records...")
        Note.query.delete()
        
        print("Deleting Session records...")
        Session.query.delete()
        
        print("Deleting Ticket records...")
        Ticket.query.delete()
        
        print("Deleting Course records...")
        Course.query.delete()
        
        print("Deleting Customer records...")
        Customer.query.delete()
        
        # Keep one admin user for system access
        print("Removing all users except admin...")
        User.query.filter(User.username != 'admin').delete()
        
        # Commit the changes
        db.session.commit()
        print("Database cleared successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing database: {str(e)}")
        raise

if __name__ == '__main__':
    # Ask for confirmation
    response = input("WARNING: This will delete all data from the database. Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        with app.app_context():  # Run within Flask application context
            clear_database()
    else:
        print("Operation cancelled.") 