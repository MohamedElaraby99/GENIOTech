from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    total_courses = Course.query.count()
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