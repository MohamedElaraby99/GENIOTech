#!/usr/bin/env python3
"""
Debug script to check SQLite database setup
"""
import os
import sqlite3
from pathlib import Path

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