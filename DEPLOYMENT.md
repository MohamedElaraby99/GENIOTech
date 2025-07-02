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

# SQLite database (default and only supported)
DATABASE_URL=sqlite:///instance/crm.db

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

# Create database backup
cp instance/crm.db backups/crm_backup_$(date +%Y%m%d_%H%M%S).db

# Restore from backup
cp backup_file.db instance/crm.db
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
   # Check SQLite database file
   ls -la /var/www/geniotech-crm/instance/

   # Check database permissions
   sudo chown -R www-data:www-data /var/www/geniotech-crm/instance/
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
curl http://localhost:8002

# Test through Nginx
curl http://localhost

# Check all services
sudo systemctl status geniotech-crm nginx
```

## 📈 Performance Optimization

### For Production Use

1. **Increase Gunicorn workers** (in `/etc/systemd/system/geniotech-crm.service`):

   ```
   ExecStart=/var/www/geniotech-crm/venv/bin/gunicorn --workers 8 --bind 0.0.0.0:8002 wsgi:application
   ```

2. **Setup Redis** for session storage (optional):

   ```bash
   sudo apt install redis-server
   ```

3. **Optimize SQLite** for better performance:
   ```bash
   # Ensure proper file permissions
   sudo chown -R www-data:www-data /var/www/geniotech-crm/instance/
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
cp /var/www/geniotech-crm/instance/crm.db /home/backups/crm_backup_$DATE.db
find /home/backups -name "crm_backup_*.db" -mtime +7 -delete
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
