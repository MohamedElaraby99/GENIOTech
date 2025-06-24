# CRM System

A comprehensive Customer Relationship Management (CRM) system built with Flask, designed for educational institutions with three distinct user roles: Admin, Instructor, and Customer Service.

## Features

### 🔐 User Authentication & Role Management

- Secure login system with role-based access control
- Three distinct user roles with tailored permissions:
  - **Admin**: Full system access, user management, reporting
  - **Instructor**: Student/customer management, session scheduling
  - **Customer Service**: Ticket management, customer support

### 👥 Customer Management

- Complete customer profile management
- Customer status tracking (Active, Needs Follow-up, No-show, Inactive)
- Instructor assignment capabilities
- Communication history and notes
- Customer detail views with comprehensive information

### 🎫 Support Ticket System

- Create and manage support tickets
- Priority levels (Low, Medium, High, Urgent)
- Ticket assignment and status tracking
- Customer-ticket relationship management
- Real-time ticket filtering and search

### 📅 Session Management

- Schedule and manage educational sessions
- Customer-instructor session assignments
- Session status tracking (Scheduled, Completed, No-show, Cancelled)
- Duration management and notes
- Calendar integration ready

### 📊 Reporting & Analytics

- Comprehensive dashboard for each user role
- Real-time statistics and metrics
- Customer status distribution
- Ticket resolution tracking
- Export capabilities (CSV, Excel, PDF)

### 🎨 Modern UI/UX

- Responsive Bootstrap 5 design
- Dark theme compatible
- Mobile-friendly interface
- Font Awesome icons
- Interactive dashboards with real-time updates

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or extract the project**

   ```bash
   cd crm
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - Login with default admin credentials:
     - Username: `admin`
     - Password: `admin123`

## Project Structure

```
crm/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── static/                         # Static assets
│   ├── css/
│   │   └── style.css              # Custom CSS styles
│   └── js/
│       └── app.js                 # JavaScript functionality
└── templates/                      # HTML templates
    ├── base.html                  # Base template
    ├── login.html                 # Login page
    ├── admin_dashboard.html       # Admin dashboard
    ├── instructor_dashboard.html  # Instructor dashboard
    ├── customer_service_dashboard.html # Customer service dashboard
    ├── customers.html             # Customer listing
    ├── add_customer.html          # Add customer form
    ├── customer_detail.html       # Customer detail view
    ├── tickets.html               # Ticket listing
    ├── add_ticket.html            # Add ticket form
    ├── sessions.html              # Session listing
    ├── add_session.html           # Add session form
    └── admin/                     # Admin-specific templates
        ├── users.html             # User management
        ├── add_user.html          # Add user form
        └── reports.html           # Reports & analytics
```

## User Roles & Permissions

### 🛡️ Admin

**Full system access with capabilities to:**

- Manage all users (create, edit, delete, assign roles)
- View comprehensive system reports and analytics
- Access all customer, ticket, and session data
- Configure system settings and workflows
- Export data in multiple formats
- Monitor system performance and user activity

### 👨‍🏫 Instructor

**Student and session management with abilities to:**

- View and manage assigned students/customers
- Schedule and manage educational sessions
- Track student progress and add notes
- View personal calendar and upcoming sessions
- Update session outcomes and completion status
- Access student communication history

### 🎧 Customer Service

**Customer support and ticket management including:**

- Create and manage support tickets
- Handle customer inquiries and complaints
- Assign tickets to appropriate personnel
- Track ticket resolution times
- Manage customer communication
- Monitor customer satisfaction metrics

## Database Schema

The system uses SQLite database with the following main entities:

- **User**: System users with role-based access
- **Customer**: Customer/student profiles and information
- **Course**: Educational courses linked to customers
- **Ticket**: Support tickets for customer assistance
- **Session**: Scheduled sessions between instructors and customers
- **Note**: Communication notes and internal messages

## API Endpoints

### Authentication

- `GET /` - Login page (redirects to dashboard if logged in)
- `POST /login` - User authentication
- `GET /logout` - User logout

### Dashboard

- `GET /dashboard` - Role-specific dashboard
- `GET /api/dashboard_stats` - Real-time dashboard statistics

### Customer Management

- `GET /customers` - Customer listing (filtered by role)
- `GET /customers/add` - Add customer form
- `POST /customers/add` - Create new customer
- `GET /customers/<id>` - Customer detail view

### Ticket Management

- `GET /tickets` - Ticket listing (filtered by role)
- `GET /tickets/add` - Add ticket form
- `POST /tickets/add` - Create new ticket

### Session Management

- `GET /sessions` - Session listing (filtered by role)
- `GET /sessions/add` - Add session form
- `POST /sessions/add` - Schedule new session

### Admin Functions

- `GET /admin/users` - User management (admin only)
- `GET /admin/users/add` - Add user form (admin only)
- `POST /admin/users/add` - Create new user (admin only)
- `GET /admin/reports` - Reports and analytics (admin only)

## Security Features

- **Password Hashing**: All passwords are securely hashed using Werkzeug
- **Session Management**: Flask-Login handles secure user sessions
- **Role-Based Access**: Decorators ensure proper permission checking
- **Input Validation**: Form validation on both client and server side
- **CSRF Protection**: Built-in Flask security features

## Customization

### Adding New Features

1. **Database Models**: Add new models in `app.py`
2. **Routes**: Create new routes with proper role decorators
3. **Templates**: Add HTML templates in the `templates/` directory
4. **Styling**: Customize CSS in `static/css/style.css`
5. **JavaScript**: Add functionality in `static/js/app.js`

### Configuration

- **Database**: Change database URL in `app.py` for production
- **Secret Key**: Update the secret key for production deployment
- **Email Settings**: Configure email settings for notifications
- **File Uploads**: Add file upload capabilities as needed

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use environment variables for sensitive configuration
2. **Database**: Migrate to PostgreSQL or MySQL for better performance
3. **Web Server**: Use Gunicorn with Nginx for production serving
4. **Security**: Implement HTTPS and additional security headers
5. **Monitoring**: Add logging and monitoring capabilities
6. **Backup**: Implement regular database backups

## Future Enhancements

- **Email Integration**: Automated email notifications
- **Calendar Integration**: Google Calendar/Outlook integration
- **File Attachments**: Document and file management
- **Advanced Reporting**: More detailed analytics and charts
- **Mobile App**: React Native or Flutter mobile application
- **API Integration**: RESTful API for third-party integrations
- **Multi-tenancy**: Support for multiple organizations

## Support

For questions, issues, or feature requests:

1. Check the existing documentation
2. Review the code comments for implementation details
3. Test with the provided sample data
4. Create detailed bug reports with steps to reproduce

## License

This project is created for educational purposes. Feel free to modify and extend according to your needs.

---

**Built with ❤️ using Flask, Bootstrap 5, and modern web technologies.**
