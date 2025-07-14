from app import app, db, User, Customer, Group, GroupMember, GroupSession, GroupAttendance, Session
from app import Note, Ticket, Performance, CourseCategory, GroupSchedule, Course
from app import CustomerHistory, GroupHistory, AuditLog, Communication

def clear_all_data():
    """Delete all data from the database while preserving table structure."""
    try:
        print("Starting database cleanup...")
        
        # Delete data in the correct order to avoid foreign key constraints
        print("Deleting communications...")
        Communication.query.delete()
        
        print("Deleting audit logs and history...")
        AuditLog.query.delete()
        CustomerHistory.query.delete()
        GroupHistory.query.delete()
        
        print("Deleting performance records...")
        Performance.query.delete()
        
        print("Deleting tickets...")
        Ticket.query.delete()
        
        print("Deleting notes...")
        Note.query.delete()
        
        print("Deleting attendance records...")
        GroupAttendance.query.delete()
        
        print("Deleting sessions...")
        GroupSession.query.delete()
        Session.query.delete()
        
        print("Deleting group relationships...")
        GroupSchedule.query.delete()
        GroupMember.query.delete()
        
        print("Deleting groups and courses...")
        Group.query.delete()
        Course.query.delete()
        
        print("Deleting categories...")
        CourseCategory.query.delete()
        
        print("Deleting customers...")
        Customer.query.delete()
        
        print("Deleting users...")
        # Keep the admin user if exists
        admin_user = User.query.filter_by(role='admin').first()
        if admin_user:
            User.query.filter(User.id != admin_user.id).delete()
            print("Kept admin user:", admin_user.email)
        else:
            User.query.delete()
        
        # Commit the changes
        db.session.commit()
        print("Database cleared successfully!")
        
    except Exception as e:
        db.session.rollback()
        print("Error clearing database:", str(e))
        raise

if __name__ == "__main__":
    # Ask for confirmation
    print("WARNING: This will delete ALL data from the database!")
    print("The table structure will be preserved, but all records will be deleted.")
    print("Only the admin user will be kept (if exists).")
    confirmation = input("Are you sure you want to continue? (yes/no): ")
    
    if confirmation.lower() == 'yes':
        with app.app_context():
            clear_all_data()
    else:
        print("Operation cancelled.") 