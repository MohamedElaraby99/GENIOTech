from app import app, db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        # Add is_active column to customer table
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE customer ADD COLUMN is_active BOOLEAN DEFAULT 1'))
            print("Added is_active column to customer table")
            
            # Set all existing customers to active
            conn.execute(text('UPDATE customer SET is_active = 1'))
            print("Set all existing customers to active")

if __name__ == '__main__':
    migrate_database() 