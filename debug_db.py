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
from sqlalchemy.exc import IntegrityError

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

def delete_group_data(group_id):
    """Delete all data associated with a specific group."""
    try:
        # Delete GroupHistory records
        GroupHistory.query.filter_by(group_id=group_id).delete()
        
        # Delete GroupAttendance records for this group's sessions
        attendance_ids = db.session.query(GroupAttendance.id).join(GroupSession).filter(GroupSession.group_id == group_id)
        GroupAttendance.query.filter(GroupAttendance.id.in_(attendance_ids)).delete(synchronize_session='fetch')
        
        # Delete GroupSession records
        GroupSession.query.filter_by(group_id=group_id).delete()
        
        # Delete GroupMember records
        GroupMember.query.filter_by(group_id=group_id).delete()
        
        # Delete GroupSchedule records
        GroupSchedule.query.filter_by(group_id=group_id).delete()
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting data for group {group_id}: {str(e)}")
        return False

def delete_customer_data(customer_id):
    """Delete all data associated with a specific customer."""
    try:
        # Delete Performance records
        Performance.query.filter_by(customer_id=customer_id).delete()
        
        # Delete Communication records
        Communication.query.filter_by(customer_id=customer_id).delete()
        
        # Delete CustomerHistory records
        CustomerHistory.query.filter_by(customer_id=customer_id).delete()
        
        # Delete GroupAttendance records
        GroupAttendance.query.join(GroupSession).join(GroupMember).filter(GroupMember.customer_id == customer_id).delete(synchronize_session='fetch')
        
        # Delete GroupMember records
        GroupMember.query.filter_by(customer_id=customer_id).delete()
        
        # Delete Notes
        Note.query.filter_by(customer_id=customer_id).delete()
        
        # Delete Sessions
        Session.query.filter_by(customer_id=customer_id).delete()
        
        # Delete Tickets
        Ticket.query.filter_by(customer_id=customer_id).delete()
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting data for customer {customer_id}: {str(e)}")
        return False

def clear_database():
    """Clear all data from the database while respecting foreign key constraints."""
    print("Starting database cleanup...")
    
    try:
        # First, get all customer IDs
        customer_ids = [c.id for c in Customer.query.all()]
        
        # Delete data for each customer
        for customer_id in customer_ids:
            print(f"Cleaning up data for customer ID {customer_id}...")
            if not delete_customer_data(customer_id):
                print(f"Skipping customer {customer_id} due to errors...")
                continue
        
        # Get all group IDs
        group_ids = [g.id for g in Group.query.all()]
        
        # Delete data for each group
        for group_id in group_ids:
            print(f"Cleaning up data for group ID {group_id}...")
            if not delete_group_data(group_id):
                print(f"Skipping group {group_id} due to errors...")
                continue
        
        # Now delete remaining records
        print("Deleting AuditLog records...")
        AuditLog.query.delete()
        
        print("Deleting remaining Group records...")
        Group.query.delete()
        
        print("Deleting CourseCategory records...")
        CourseCategory.query.delete()
        
        print("Deleting Course records...")
        Course.query.delete()
        
        print("Deleting remaining Customer records...")
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