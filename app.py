from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import pandas as pd
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add nl2br filter for templates
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags"""
    if value:
        return value.replace('\n', '<br>\n')
    return value

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, instructor, customer_service
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')  # active, inactive, needs_follow_up, no_show
    assigned_instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    initial_notes = db.Column(db.Text)
    
    assigned_instructor = db.relationship('User', backref='assigned_customers')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, cancelled
    scheduled_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completion_notes = db.Column(db.Text)
    
    customer = db.relationship('Customer', backref='courses')
    instructor = db.relationship('User', backref='assigned_courses')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    customer = db.relationship('Customer', backref='tickets')
    assigned_to = db.relationship('User', backref='assigned_tickets')

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, default=60)  # minutes
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, no_show, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='sessions')
    instructor = db.relationship('User', backref='instructor_sessions')
    course = db.relationship('Course', backref='sessions')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_internal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    customer = db.relationship('Customer', backref='notes_list')
    created_by = db.relationship('User', backref='created_notes')

# New Course Management Models
class CourseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GeneralCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('course_category.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    duration_hours = db.Column(db.Integer, default=10)  # Total course duration
    price = db.Column(db.Float, default=0.0)
    max_students = db.Column(db.Integer, default=20)
    status = db.Column(db.String(20), default='active')  # active, inactive, archived
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('CourseCategory', backref='courses')
    instructor = db.relationship('User', backref='taught_courses')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('general_course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, dropped, suspended
    progress = db.Column(db.Float, default=0.0)  # Percentage completion
    final_grade = db.Column(db.String(10))  # A, B, C, D, F
    completion_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    customer = db.relationship('Customer', backref='enrollments')
    course = db.relationship('GeneralCourse', backref='enrollments')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password) and user.is_active:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return render_template('admin_dashboard.html')
    elif current_user.role == 'instructor':
        return render_template('instructor_dashboard.html')
    elif current_user.role == 'customer_service':
        return render_template('customer_service_dashboard.html')
    else:
        flash('Invalid user role', 'error')
        return redirect(url_for('logout'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user profile
        current_user.first_name = request.form['first_name']
        current_user.last_name = request.form['last_name']
        current_user.email = request.form['email']
        
        # Update password if provided
        if request.form.get('current_password') and request.form.get('new_password'):
            if check_password_hash(current_user.password_hash, request.form['current_password']):
                if request.form['new_password'] == request.form['confirm_password']:
                    current_user.password_hash = generate_password_hash(request.form['new_password'])
                    flash('Profile and password updated successfully!', 'success')
                else:
                    flash('New passwords do not match!', 'error')
                    return render_template('profile.html')
            else:
                flash('Current password is incorrect!', 'error')
                return render_template('profile.html')
        else:
            flash('Profile updated successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

# Admin Routes
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password_hash=generate_password_hash(request.form['password']),
            role=request.form['role'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name']
        )
        db.session.add(user)
        db.session.commit()
        flash('User added successfully', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/add_user.html')

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.role = request.form['role']
        user.is_active = 'is_active' in request.form
        
        # Update password if provided
        if request.form.get('password'):
            user.password_hash = generate_password_hash(request.form['password'])
        
        try:
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating user: Username or email may already exist', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the current admin user
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    # Check if user has assigned customers or tickets
    if user.assigned_customers or user.assigned_tickets or user.instructor_sessions:
        flash('Cannot delete user with assigned customers, tickets, or sessions. Please reassign them first.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent toggling the current admin user
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    status = 'activated' if user.is_active else 'deactivated'
    
    try:
        db.session.commit()
        flash(f'User {user.username} has been {status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating user status', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    # Calculate statistics
    total_customers = Customer.query.count()
    total_courses = GeneralCourse.query.count()
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter_by(status='open').count()
    resolved_tickets = Ticket.query.filter_by(status='resolved').count()
    
    # Recent activities
    recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(5).all()
    recent_tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(5).all()
    
    stats = {
        'total_customers': total_customers,
        'total_courses': total_courses,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'resolved_tickets': resolved_tickets
    }
    
    return render_template('admin/reports.html', stats=stats, 
                         recent_customers=recent_customers, recent_tickets=recent_tickets)

# Customer Management Routes
@app.route('/customers')
@login_required
def customers():
    if current_user.role == 'instructor':
        customers = Customer.query.filter_by(assigned_instructor_id=current_user.id).all()
    else:
        customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        customer = Customer(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone=request.form.get('phone', ''),
            assigned_instructor_id=request.form.get('assigned_instructor_id') or None,
            initial_notes=request.form.get('notes', '')
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully', 'success')
        return redirect(url_for('customers'))
    
    instructors = User.query.filter_by(role='instructor').all()
    return render_template('add_customer.html', instructors=instructors)

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Check permissions
    if current_user.role == 'instructor' and customer.assigned_instructor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        customer.first_name = request.form['first_name']
        customer.last_name = request.form['last_name']
        customer.email = request.form['email']
        customer.phone = request.form.get('phone', '')
        customer.status = request.form['status']
        
        # Only admins and customer service can change instructor assignment
        if current_user.role in ['admin', 'customer_service']:
            customer.assigned_instructor_id = request.form.get('assigned_instructor_id') or None
        
        try:
            db.session.commit()
            flash('Customer updated successfully', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating customer: Email may already exist', 'error')
    
    instructors = User.query.filter_by(role='instructor').all()
    return render_template('edit_customer.html', customer=customer, instructors=instructors)

@app.route('/customers/<int:customer_id>/add_note', methods=['POST'])
@login_required
def add_customer_note(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Check permissions
    if current_user.role == 'instructor' and customer.assigned_instructor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('customers'))
    
    content = request.form.get('note_content')
    is_internal = 'is_internal' in request.form
    
    if content:
        note = Note(
            content=content,
            customer_id=customer_id,
            created_by_id=current_user.id,
            is_internal=is_internal
        )
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully', 'success')
    else:
        flash('Note content cannot be empty', 'error')
    
    return redirect(url_for('customer_detail', customer_id=customer_id))

@app.route('/customers/campaign', methods=['POST'])
@login_required
def send_whatsapp_campaign():
    selected_customers = request.form.getlist('selected_customers')
    message_template = request.form.get('message_template', '')
    
    if not selected_customers:
        flash('Please select at least one customer', 'error')
        return redirect(url_for('customers'))
    
    if not message_template:
        flash('Please enter a message template', 'error')
        return redirect(url_for('customers'))
    
    # Get selected customers
    if current_user.role == 'instructor':
        customers = Customer.query.filter(
            Customer.id.in_(selected_customers),
            Customer.assigned_instructor_id == current_user.id
        ).all()
    else:
        customers = Customer.query.filter(Customer.id.in_(selected_customers)).all()
    
    # Generate WhatsApp links
    whatsapp_links = []
    for customer in customers:
        if customer.phone:
            # Replace template variables
            personalized_message = message_template.replace('{name}', f"{customer.first_name} {customer.last_name}")
            personalized_message = personalized_message.replace('{first_name}', customer.first_name)
            personalized_message = personalized_message.replace('{last_name}', customer.last_name)
            
            # Clean phone number (remove spaces, dashes, etc.)
            clean_phone = ''.join(filter(str.isdigit, customer.phone))
            
            # Create WhatsApp Web link
            whatsapp_url = f"https://wa.me/{clean_phone}?text={personalized_message}"
            whatsapp_links.append({
                'customer': customer,
                'url': whatsapp_url,
                'message': personalized_message
            })
    
    # For now, we'll return the links to the user to open manually
    # In a real application, you might want to integrate with WhatsApp Business API
    return render_template('campaign_results.html', 
                         whatsapp_links=whatsapp_links, 
                         message_template=message_template)

@app.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Check permissions
    if current_user.role == 'instructor' and customer.assigned_instructor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('customers'))
    
    notes = Note.query.filter_by(customer_id=customer_id).order_by(Note.created_at.desc()).all()
    tickets = Ticket.query.filter_by(customer_id=customer_id).order_by(Ticket.created_at.desc()).all()
    courses = Course.query.filter_by(customer_id=customer_id).order_by(Course.created_at.desc()).all()
    sessions = Session.query.filter_by(customer_id=customer_id).order_by(Session.scheduled_date.desc()).all()
    
    return render_template('customer_detail.html', customer=customer, notes=notes, 
                         tickets=tickets, courses=courses, sessions=sessions)

# Excel Import Routes
@app.route('/customers/import-template')
@login_required
def download_customer_template():
    """Download Excel template for customer import"""
    # Create a sample Excel file
    data = {
        'first_name': ['محمد', 'فاطمة', 'أحمد'],
        'last_name': ['أحمد', 'سالم', 'محمود'],
        'email': ['mohammed@example.com', 'fatima@example.com', 'ahmed@example.com'],
        'phone': ['+966501234567', '+966507654321', '+966509876543'],
        'status': ['active', 'active', 'needs_follow_up'],
        'assigned_instructor_email': ['instructor@example.com', '', 'instructor@example.com'],
        'initial_notes': ['ملاحظات أولية للعميل', 'عميل مهتم بدورات البرمجة', 'يحتاج متابعة خاصة']
    }
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write the template data
        df.to_excel(writer, sheet_name='Customers Template', index=False)
        
        # Get workbook and worksheet for formatting
        workbook = writer.book
        worksheet = writer.sheets['Customers Template']
        
        # Create header style
        from openpyxl.styles import Font, PatternFill, Alignment
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        # Apply header formatting
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Add instructions sheet
        instructions_data = {
            'Column Name': [
                'first_name',
                'last_name', 
                'email',
                'phone',
                'status',
                'assigned_instructor_email',
                'initial_notes'
            ],
            'Required': [
                'Yes',
                'Yes',
                'Yes', 
                'No',
                'No',
                'No',
                'No'
            ],
            'Description': [
                'الاسم الأول للعميل',
                'اسم العائلة للعميل',
                'البريد الإلكتروني (يجب أن يكون فريد)',
                'رقم الهاتف (مع رمز الدولة)',
                'حالة العميل: active, inactive, needs_follow_up, no_show',
                'البريد الإلكتروني للمدرب المسؤول (اختياري)',
                'ملاحظات أولية عن العميل'
            ],
            'Example': [
                'محمد',
                'أحمد',
                'mohammed@example.com',
                '+966501234567',
                'active',
                'instructor@example.com',
                'عميل مهتم بدورات البرمجة'
            ]
        }
        
        instructions_df = pd.DataFrame(instructions_data)
        instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Format instructions sheet
        instructions_sheet = writer.sheets['Instructions']
        for cell in instructions_sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Auto-adjust column widths for instructions
        for column in instructions_sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 60)
            instructions_sheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=customer_import_template_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    return response

@app.route('/customers/import', methods=['GET', 'POST'])
@login_required
def import_customers():
    """Import customers from Excel file"""
    if request.method == 'GET':
        return render_template('import_customers.html')
    
    # Handle file upload
    if 'excel_file' not in request.files:
        flash('يرجى اختيار ملف Excel', 'error')
        return redirect(request.url)
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('لم يتم اختيار أي ملف', 'error')
        return redirect(request.url)
    
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        flash('يرجى رفع ملف Excel فقط (.xlsx أو .xls)', 'error')
        return redirect(request.url)
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Debug: Show what columns were found
        found_columns = list(df.columns)
        print(f"Found columns in Excel: {found_columns}")
        
        # Clean column names (remove extra spaces, etc.)
        df.columns = df.columns.str.strip()
        
        # Validate required columns
        required_columns = ['first_name', 'last_name', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            flash(f'الأعمدة التالية مطلوبة ومفقودة: {", ".join(missing_columns)}', 'error')
            flash(f'الأعمدة الموجودة في الملف: {", ".join(found_columns)}', 'info')
            flash('يرجى التأكد من أن أسماء الأعمدة مطابقة تماماً: first_name, last_name, email', 'info')
            return redirect(request.url)
        
        # Import statistics
        imported_count = 0
        skipped_count = 0
        error_messages = []
        
        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row['first_name']) or pd.isna(row['last_name']) or pd.isna(row['email']):
                    skipped_count += 1
                    continue
                
                # Check if customer already exists
                existing_customer = Customer.query.filter_by(email=row['email']).first()
                if existing_customer:
                    error_messages.append(f'الصف {index + 2}: العميل بالبريد الإلكتروني {row["email"]} موجود مسبقاً')
                    skipped_count += 1
                    continue
                
                # Find assigned instructor if specified
                assigned_instructor = None
                if not pd.isna(row.get('assigned_instructor_email')):
                    assigned_instructor = User.query.filter_by(
                        email=row['assigned_instructor_email'],
                        role='instructor'
                    ).first()
                    if not assigned_instructor:
                        error_messages.append(f'الصف {index + 2}: المدرب بالبريد الإلكتروني {row["assigned_instructor_email"]} غير موجود')
                
                # Validate status
                valid_statuses = ['active', 'inactive', 'needs_follow_up', 'no_show']
                status = row.get('status', 'active')
                if pd.isna(status):
                    status = 'active'
                if status not in valid_statuses:
                    status = 'active'
                
                # Create customer
                customer = Customer(
                    first_name=str(row['first_name']).strip(),
                    last_name=str(row['last_name']).strip(),
                    email=str(row['email']).strip().lower(),
                    phone=str(row.get('phone', '')).strip() if not pd.isna(row.get('phone')) else '',
                    status=status,
                    assigned_instructor_id=assigned_instructor.id if assigned_instructor else None,
                    initial_notes=str(row.get('initial_notes', '')).strip() if not pd.isna(row.get('initial_notes')) else ''
                )
                
                db.session.add(customer)
                imported_count += 1
                
            except Exception as e:
                error_messages.append(f'الصف {index + 2}: خطأ في الاستيراد - {str(e)}')
                skipped_count += 1
        
        # Commit changes
        try:
            db.session.commit()
            
            # Success message
            success_msg = f'تم استيراد {imported_count} عميل بنجاح'
            if skipped_count > 0:
                success_msg += f', تم تخطي {skipped_count} صف'
            flash(success_msg, 'success')
            
            # Show errors if any
            if error_messages:
                for error in error_messages[:10]:  # Show first 10 errors
                    flash(error, 'warning')
                if len(error_messages) > 10:
                    flash(f'وهناك {len(error_messages) - 10} أخطاء إضافية...', 'warning')
            
            return redirect(url_for('customers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء حفظ البيانات: {str(e)}', 'error')
            return redirect(request.url)
            
    except Exception as e:
        flash(f'خطأ في قراءة ملف Excel: {str(e)}', 'error')
        return redirect(request.url)

# Ticket Management Routes
@app.route('/tickets')
@login_required
def tickets():
    if current_user.role == 'customer_service':
        tickets = Ticket.query.filter_by(assigned_to_id=current_user.id).all()
    else:
        tickets = Ticket.query.all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/tickets/add', methods=['GET', 'POST'])
@login_required
def add_ticket():
    if request.method == 'POST':
        ticket = Ticket(
            title=request.form['title'],
            description=request.form['description'],
            customer_id=request.form['customer_id'],
            assigned_to_id=request.form.get('assigned_to_id') or None,
            priority=request.form['priority']
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Ticket created successfully', 'success')
        return redirect(url_for('tickets'))
    
    customers = Customer.query.all()
    agents = User.query.filter_by(role='customer_service').all()
    return render_template('add_ticket.html', customers=customers, agents=agents)

@app.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if current_user.role == 'customer_service' and ticket.assigned_to_id != current_user.id:
        flash('Access denied. You can only view tickets assigned to you.', 'error')
        return redirect(url_for('tickets'))
    
    return render_template('ticket_detail.html', ticket=ticket)

@app.route('/tickets/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if current_user.role == 'customer_service' and ticket.assigned_to_id != current_user.id:
        flash('Access denied. You can only edit tickets assigned to you.', 'error')
        return redirect(url_for('tickets'))
    
    if request.method == 'POST':
        ticket.title = request.form['title']
        ticket.description = request.form['description']
        ticket.priority = request.form['priority']
        ticket.status = request.form['status']
        
        # Only admins can reassign tickets
        if current_user.role == 'admin':
            ticket.assigned_to_id = request.form.get('assigned_to_id') or None
        
        # Update resolution info if status is resolved
        if ticket.status == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
            ticket.resolution_notes = request.form.get('resolution_notes', '')
        elif ticket.status != 'resolved':
            ticket.resolved_at = None
            ticket.resolution_notes = None
        
        db.session.commit()
        flash('Ticket updated successfully', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    
    customers = Customer.query.all()
    agents = User.query.filter_by(role='customer_service').all()
    return render_template('edit_ticket.html', ticket=ticket, customers=customers, agents=agents)

@app.route('/tickets/<int:ticket_id>/resolve', methods=['POST'])
@login_required
def resolve_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if current_user.role == 'customer_service' and ticket.assigned_to_id != current_user.id:
        flash('Access denied. You can only resolve tickets assigned to you.', 'error')
        return redirect(url_for('tickets'))
    
    ticket.status = 'resolved'
    ticket.resolved_at = datetime.utcnow()
    ticket.resolution_notes = request.form.get('resolution_notes', '')
    
    db.session.commit()
    flash('Ticket marked as resolved', 'success')
    return redirect(url_for('tickets'))

# Session/Schedule Management Routes
@app.route('/sessions')
@login_required
def sessions():
    if current_user.role == 'instructor':
        sessions = Session.query.filter_by(instructor_id=current_user.id).order_by(Session.scheduled_date).all()
    else:
        sessions = Session.query.order_by(Session.scheduled_date).all()
    return render_template('sessions.html', sessions=sessions)

@app.route('/sessions/add', methods=['GET', 'POST'])
@login_required
def add_session():
    if request.method == 'POST':
        session_obj = Session(
            customer_id=request.form['customer_id'],
            instructor_id=request.form['instructor_id'],
            course_id=request.form.get('course_id') or None,
            scheduled_date=datetime.strptime(request.form['scheduled_date'], '%Y-%m-%dT%H:%M'),
            duration=int(request.form['duration']),
            notes=request.form.get('notes', '')
        )
        db.session.add(session_obj)
        db.session.commit()
        flash('Session scheduled successfully', 'success')
        return redirect(url_for('sessions'))
    
    customers = Customer.query.all()
    instructors = User.query.filter_by(role='instructor').all()
    courses = Course.query.all()
    return render_template('add_session.html', customers=customers, instructors=instructors, courses=courses)

# API Routes for AJAX
@app.route('/api/dashboard_stats')
@login_required
def api_dashboard_stats():
    if current_user.role == 'admin':
        stats = {
            'total_users': User.query.count(),
            'total_customers': Customer.query.count(),
            'total_tickets': Ticket.query.count(),
            'open_tickets': Ticket.query.filter_by(status='open').count()
        }
    elif current_user.role == 'instructor':
        stats = {
            'my_customers': Customer.query.filter_by(assigned_instructor_id=current_user.id).count(),
            'today_sessions': Session.query.filter_by(instructor_id=current_user.id).filter(
                Session.scheduled_date >= datetime.now().date(),
                Session.scheduled_date < datetime.now().date() + timedelta(days=1)
            ).count(),
            'completed_sessions': Session.query.filter_by(instructor_id=current_user.id, status='completed').count()
        }
    elif current_user.role == 'customer_service':
        stats = {
            'my_tickets': Ticket.query.filter_by(assigned_to_id=current_user.id).count(),
            'open_tickets': Ticket.query.filter_by(assigned_to_id=current_user.id, status='open').count(),
            'resolved_today': Ticket.query.filter_by(assigned_to_id=current_user.id, status='resolved').filter(
                Ticket.resolved_at >= datetime.now().date()
            ).count()
        }
    
    return jsonify(stats)

# Course Management Routes
@app.route('/courses')
@login_required
def courses():
    if current_user.role == 'instructor':
        courses = GeneralCourse.query.filter_by(instructor_id=current_user.id).all()
    else:
        courses = GeneralCourse.query.all()
    
    categories = CourseCategory.query.all()
    return render_template('courses.html', courses=courses, categories=categories)

@app.route('/courses/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        course = GeneralCourse(
            title=request.form['title'],
            description=request.form['description'],
            category_id=request.form.get('category_id') or None,
            instructor_id=request.form['instructor_id'],
            duration_hours=int(request.form['duration_hours']),
            price=float(request.form['price']),
            max_students=int(request.form['max_students']),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d') if request.form['start_date'] else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form['end_date'] else None
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully', 'success')
        return redirect(url_for('courses'))
    
    categories = CourseCategory.query.all()
    instructors = User.query.filter_by(role='instructor').all()
    return render_template('add_course.html', categories=categories, instructors=instructors)

@app.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    course = GeneralCourse.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('courses'))
    
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    
    # Get customers not already enrolled in this course
    enrolled_customer_ids = [e.customer_id for e in enrollments if e.status == 'active']
    available_customers = Customer.query.filter(~Customer.id.in_(enrolled_customer_ids)).all()
    
    return render_template('course_detail.html', course=course, enrollments=enrollments, available_customers=available_customers)

@app.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = GeneralCourse.query.get_or_404(course_id)
    
    # Check permissions
    if current_user.role == 'instructor' and course.instructor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('courses'))
    
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.category_id = request.form.get('category_id') or None
        course.duration_hours = int(request.form['duration_hours'])
        course.price = float(request.form['price'])
        course.max_students = int(request.form['max_students'])
        course.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d') if request.form['start_date'] else None
        course.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form['end_date'] else None
        course.status = request.form['status']
        
        # Only admins can change instructor
        if current_user.role == 'admin':
            course.instructor_id = request.form['instructor_id']
        
        db.session.commit()
        flash('Course updated successfully', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
    
    categories = CourseCategory.query.all()
    instructors = User.query.filter_by(role='instructor').all()
    return render_template('edit_course.html', course=course, categories=categories, instructors=instructors)

@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_student(course_id):
    course = GeneralCourse.query.get_or_404(course_id)
    customer_id = request.form.get('customer_id')
    
    if not customer_id:
        flash('Please select a student', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Check if already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        customer_id=customer_id, 
        course_id=course_id, 
        status='active'
    ).first()
    
    if existing_enrollment:
        flash('Student is already enrolled in this course', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Check if course is full
    current_enrollments = Enrollment.query.filter_by(course_id=course_id, status='active').count()
    if current_enrollments >= course.max_students:
        flash('Course is full', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    enrollment = Enrollment(
        customer_id=customer_id,
        course_id=course_id
    )
    db.session.add(enrollment)
    db.session.commit()
    
    flash('Student enrolled successfully', 'success')
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/enrollments/<int:enrollment_id>/update', methods=['POST'])
@login_required
def update_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    # Check permissions
    if current_user.role == 'instructor' and enrollment.course.instructor_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('courses'))
    
    enrollment.status = request.form.get('status', enrollment.status)
    enrollment.progress = float(request.form.get('progress', enrollment.progress))
    enrollment.final_grade = request.form.get('final_grade', enrollment.final_grade)
    enrollment.notes = request.form.get('notes', enrollment.notes)
    
    if enrollment.status == 'completed' and not enrollment.completion_date:
        enrollment.completion_date = datetime.utcnow()
    
    db.session.commit()
    flash('Enrollment updated successfully', 'success')
    return redirect(url_for('course_detail', course_id=enrollment.course_id))

# Course Categories Management
@app.route('/admin/categories')
@admin_required
def admin_categories():
    categories = CourseCategory.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def admin_add_category():
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        category = CourseCategory(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully', 'success')
    else:
        flash('Category name is required', 'error')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<int:category_id>/edit', methods=['POST'])
@admin_required
def admin_edit_category(category_id):
    category = CourseCategory.query.get_or_404(category_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        category.name = name
        category.description = description
        db.session.commit()
        flash('Category updated successfully', 'success')
    else:
        flash('Category name is required', 'error')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    category = CourseCategory.query.get_or_404(category_id)
    
    # Check if category has courses
    if category.courses:
        flash('Cannot delete category with existing courses', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully', 'success')
    
    return redirect(url_for('admin_categories'))

# Report Generation Routes
@app.route('/admin/reports/customers/csv')
@admin_required
def export_customers_csv():
    # Get all customers with related data
    customers = Customer.query.all()
    
    # Prepare data for CSV
    data = []
    for customer in customers:
        data.append({
            'ID': customer.id,
            'First Name': customer.first_name,
            'Last Name': customer.last_name,
            'Email': customer.email,
            'Phone': customer.phone or '',
            'Status': customer.status,
            'Assigned Instructor': f"{customer.assigned_instructor.first_name} {customer.assigned_instructor.last_name}" if customer.assigned_instructor else 'Unassigned',
            'Created Date': customer.created_at.strftime('%Y-%m-%d'),
            'Notes': customer.initial_notes or '',
            'Total Sessions': len(customer.sessions),
            'Total Tickets': len(customer.tickets),
            'Active Enrollments': len([e for e in customer.enrollments if e.status == 'active'])
        })
    
    # Create DataFrame and convert to CSV
    df = pd.DataFrame(data)
    
    # Create CSV response
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=customers_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

@app.route('/admin/reports/tickets/excel')
@admin_required
def export_tickets_excel():
    # Get all tickets with related data
    tickets = Ticket.query.all()
    
    # Prepare data for Excel
    data = []
    for ticket in tickets:
        data.append({
            'Ticket ID': ticket.id,
            'Title': ticket.title,
            'Description': ticket.description[:100] + '...' if len(ticket.description) > 100 else ticket.description,
            'Customer': f"{ticket.customer.first_name} {ticket.customer.last_name}",
            'Customer Email': ticket.customer.email,
            'Assigned To': f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}" if ticket.assigned_to else 'Unassigned',
            'Status': ticket.status,
            'Priority': ticket.priority,
            'Created Date': ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            'Resolved Date': ticket.resolved_at.strftime('%Y-%m-%d %H:%M') if ticket.resolved_at else 'Not Resolved',
            'Resolution Notes': ticket.resolution_notes or ''
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Tickets Report', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Tickets Report']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = f'attachment; filename=tickets_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return response

@app.route('/admin/reports/summary/pdf')
@admin_required
def export_summary_pdf():
    # Get statistics
    total_customers = Customer.query.count()
    total_courses = GeneralCourse.query.count()
    total_tickets = Ticket.query.count()
    total_enrollments = Enrollment.query.count()
    
    open_tickets = Ticket.query.filter_by(status='open').count()
    resolved_tickets = Ticket.query.filter_by(status='resolved').count()
    
    active_customers = Customer.query.filter_by(status='active').count()
    active_courses = GeneralCourse.query.filter_by(status='active').count()
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Title
    title = Paragraph("GENIO TECH CRM - Summary Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Report date
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Overview Section
    overview_title = Paragraph("System Overview", heading_style)
    elements.append(overview_title)
    
    overview_data = [
        ['Metric', 'Count'],
        ['Total Customers', str(total_customers)],
        ['Active Customers', str(active_customers)],
        ['Total Courses', str(total_courses)],
        ['Active Courses', str(active_courses)],
        ['Total Enrollments', str(total_enrollments)],
        ['Total Tickets', str(total_tickets)],
        ['Open Tickets', str(open_tickets)],
        ['Resolved Tickets', str(resolved_tickets)]
    ]
    
    overview_table = Table(overview_data, colWidths=[3*inch, 2*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(overview_table)
    elements.append(Spacer(1, 20))
    
    # Customer Status Breakdown
    customer_title = Paragraph("Customer Status Breakdown", heading_style)
    elements.append(customer_title)
    
    customer_statuses = {}
    for status in ['active', 'inactive', 'needs_follow_up', 'no_show']:
        count = Customer.query.filter_by(status=status).count()
        customer_statuses[status.replace('_', ' ').title()] = count
    
    customer_data = [['Status', 'Count']]
    for status, count in customer_statuses.items():
        customer_data.append([status, str(count)])
    
    customer_table = Table(customer_data, colWidths=[3*inch, 2*inch])
    customer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(customer_table)
    elements.append(Spacer(1, 20))
    
    # Recent Activity
    activity_title = Paragraph("Recent Activity (Last 30 Days)", heading_style)
    elements.append(activity_title)
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_customers = Customer.query.filter(Customer.created_at >= thirty_days_ago).count()
    recent_tickets = Ticket.query.filter(Ticket.created_at >= thirty_days_ago).count()
    recent_enrollments = Enrollment.query.filter(Enrollment.enrollment_date >= thirty_days_ago).count()
    
    activity_data = [
        ['Activity', 'Count'],
        ['New Customers', str(recent_customers)],
        ['New Tickets', str(recent_tickets)],
        ['New Enrollments', str(recent_enrollments)]
    ]
    
    activity_table = Table(activity_data, colWidths=[3*inch, 2*inch])
    activity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(activity_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer = Paragraph("Generated by GENIO TECH CRM System", styles['Normal'])
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=summary_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    return response

@app.route('/admin/reports/analytics')
@admin_required
def analytics_dashboard():
    # Generate analytics charts and data
    
    # Customer registration trend (last 12 months)
    months = []
    customer_counts = []
    for i in range(12):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        count = Customer.query.filter(
            Customer.created_at >= month_start,
            Customer.created_at <= month_end
        ).count()
        months.append(month_start.strftime('%b %Y'))
        customer_counts.append(count)
    
    months.reverse()
    customer_counts.reverse()
    
    # Create customer trend chart
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 2, 1)
    plt.plot(months, customer_counts, marker='o', linewidth=2, markersize=6)
    plt.title('Customer Registration Trend (12 Months)', fontsize=14, fontweight='bold')
    plt.xlabel('Month')
    plt.ylabel('New Customers')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    # Ticket status distribution
    plt.subplot(2, 2, 2)
    ticket_statuses = ['open', 'in_progress', 'resolved', 'closed']
    ticket_counts = [Ticket.query.filter_by(status=status).count() for status in ticket_statuses]
    colors_pie = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    
    # Check if we have any ticket data
    if sum(ticket_counts) > 0:
        # Filter out zero counts for better pie chart
        non_zero_data = [(status, count, color) for status, count, color in zip(ticket_statuses, ticket_counts, colors_pie) if count > 0]
        if non_zero_data:
            filtered_statuses, filtered_counts, filtered_colors = zip(*non_zero_data)
            plt.pie(filtered_counts, labels=filtered_statuses, autopct='%1.1f%%', colors=filtered_colors)
        else:
            plt.pie([1], labels=['No Data'], colors=['#cccccc'])
    else:
        plt.pie([1], labels=['No Tickets'], colors=['#cccccc'])
    plt.title('Ticket Status Distribution', fontsize=14, fontweight='bold')
    
    # Course enrollment stats
    plt.subplot(2, 2, 3)
    courses = GeneralCourse.query.all()
    course_names = [course.title[:15] + '...' if len(course.title) > 15 else course.title for course in courses[:5]]
    enrollment_counts = [len(course.enrollments) for course in courses[:5]]
    plt.bar(course_names, enrollment_counts, color='skyblue')
    plt.title('Top 5 Courses by Enrollment', fontsize=14, fontweight='bold')
    plt.xlabel('Course')
    plt.ylabel('Enrollments')
    plt.xticks(rotation=45)
    
    # Customer status distribution
    plt.subplot(2, 2, 4)
    customer_statuses = ['active', 'inactive', 'needs_follow_up', 'no_show']
    customer_status_counts = [Customer.query.filter_by(status=status).count() for status in customer_statuses]
    plt.bar(customer_statuses, customer_status_counts, color=['green', 'gray', 'orange', 'red'])
    plt.title('Customer Status Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Status')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save chart to base64 string
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    
    # Convert to base64
    chart_data = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    # Calculate additional statistics
    stats = {
        'total_customers': Customer.query.count(),
        'total_courses': GeneralCourse.query.count(),
        'total_tickets': Ticket.query.count(),
        'total_enrollments': Enrollment.query.count(),
        'resolution_rate': (Ticket.query.filter_by(status='resolved').count() / max(Ticket.query.count(), 1)) * 100,
        'active_course_rate': (GeneralCourse.query.filter_by(status='active').count() / max(GeneralCourse.query.count(), 1)) * 100,
        'average_enrollments_per_course': Enrollment.query.count() / max(GeneralCourse.query.count(), 1)
    }
    
    return render_template('admin/analytics.html', chart_data=chart_data, stats=stats)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                first_name='System',
                last_name='Administrator'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: username='admin', password='admin123'")
    
    app.run(debug=True) 