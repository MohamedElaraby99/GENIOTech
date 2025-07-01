# 🚀 GENIO TECH CRM - VPS Deployment Guide

This guide will help you deploy the GENIO TECH CRM system on a VPS server (Ubuntu 20.04/22.04).

## 📋 Prerequisites

- Ubuntu 20.04 or 22.04 VPS server
- Root or sudo access
- Domain name pointed to your server (optional, for SSL)
- At least 2GB RAM and 20GB storage

## 🔧 Quick Deployment

### Step 1: Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clone the project
git clone <your-repository-url> /tmp/geniotech-crm
cd /tmp/geniotech-crm

# Make scripts executable
chmod +x deploy.sh setup_services.sh setup_ssl.sh
```

### Step 2: Deploy the Application

```bash
# Run the deployment script
./deploy.sh
```

### Step 3: Setup Services

```bash
# Setup database, nginx, and systemd services (requires sudo)
sudo ./setup_services.sh
```

### Step 4: Configure Environment (Important!)

```bash
# Edit the environment file
sudo nano /var/www/geniotech-crm/.env
```

Update these important settings:

```env
# Change the secret key for security
SECRET_KEY=your-super-secret-key-here

# Update database URL if using PostgreSQL
DATABASE_URL=postgresql://geniotech_user:your_password@localhost/geniotech_crm

# Set your domain (if applicable)
SERVER_NAME=your-domain.com
```

### Step 5: Initialize Database

```bash
cd /var/www/geniotech-crm
source venv/bin/activate
python wsgi.py
# This will create the database tables and default admin user
```

### Step 6: Start Services

```bash
sudo systemctl restart geniotech-crm
sudo systemctl restart nginx
```

## 🔐 SSL Setup (Optional but Recommended)

If you have a domain name:

```bash
# Setup SSL certificate with Let's Encrypt
sudo ./setup_ssl.sh your-domain.com
```

## 📁 Directory Structure

```
/var/www/geniotech-crm/
├── app.py                 # Main application
├── wsgi.py               # WSGI entry point
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── venv/                 # Python virtual environment
├── instance/            # Database and instance files
├── temp/                # Temporary uploads
├── logs/                # Application logs
├── static/              # Static files (CSS, JS, images)
└── templates/           # HTML templates
```

## 🛠️ Management Commands

The deployment creates a management script at `/var/www/geniotech-crm/manage.sh`:

```bash
# Start the application
sudo /var/www/geniotech-crm/manage.sh start

# Stop the application
sudo /var/www/geniotech-crm/manage.sh stop

# Restart the application
sudo /var/www/geniotech-crm/manage.sh restart

# Check status
sudo /var/www/geniotech-crm/manage.sh status

# View logs
sudo /var/www/geniotech-crm/manage.sh logs

# Update application
sudo /var/www/geniotech-crm/manage.sh update
```

## 🔧 Manual Commands

### Service Management

```bash
# Check application status
sudo systemctl status geniotech-crm

# View application logs
sudo journalctl -u geniotech-crm -f

# Restart services
sudo systemctl restart geniotech-crm
sudo systemctl restart nginx
```

### Database Operations

```bash
cd /var/www/geniotech-crm
source venv/bin/activate

# Create database backup
pg_dump geniotech_crm > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql geniotech_crm < backup_file.sql
```

## 🔐 Security Checklist

- [ ] Change default admin password
- [ ] Update SECRET_KEY in .env file
- [ ] Configure SSL certificate
- [ ] Setup firewall (UFW)
- [ ] Regular security updates
- [ ] Database backups

## 🌐 Accessing the Application

- **HTTP:** `http://your-server-ip`
- **HTTPS:** `https://your-domain.com` (after SSL setup)

### Default Login Credentials

- **Username:** `admin`
- **Password:** `admin123`

⚠️ **Important:** Change the default password immediately after first login!

## 🐛 Troubleshooting

### Common Issues

1. **Service won't start**

   ```bash
   sudo journalctl -u geniotech-crm -n 50
   ```

2. **Database connection errors**

   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql

   # Check database exists
   sudo -u postgres psql -l
   ```

3. **Nginx errors**

   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Permission issues**
   ```bash
   sudo chown -R www-data:www-data /var/www/geniotech-crm
   sudo chmod -R 755 /var/www/geniotech-crm
   ```

### Check Application Health

```bash
# Test application directly
curl http://localhost:8000

# Test through Nginx
curl http://localhost

# Check all services
sudo systemctl status geniotech-crm nginx postgresql
```

## 📈 Performance Optimization

### For Production Use

1. **Increase Gunicorn workers** (in `/etc/systemd/system/geniotech-crm.service`):

   ```
   ExecStart=/var/www/geniotech-crm/venv/bin/gunicorn --workers 8 --bind 0.0.0.0:8000 wsgi:application
   ```

2. **Configure PostgreSQL** for better performance:

   ```bash
   sudo nano /etc/postgresql/*/main/postgresql.conf
   ```

3. **Setup Redis** for session storage (optional):
   ```bash
   sudo apt install redis-server
   ```

## 🔄 Updates and Maintenance

### Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update application
cd /var/www/geniotech-crm
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart geniotech-crm
```

### Database Backup Script

Create `/home/backup_db.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump geniotech_crm > /home/backups/geniotech_crm_$DATE.sql
find /home/backups -name "geniotech_crm_*.sql" -mtime +7 -delete
```

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /home/backup_db.sh
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs: `sudo journalctl -u geniotech-crm -f`
3. Check system resources: `htop` or `top`
4. Verify network connectivity and DNS

## 🔗 Additional Resources

- [Flask Deployment Documentation](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0
