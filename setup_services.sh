#!/bin/bash
# Services setup script for GENIO TECH CRM (run as root)

set -e

# Configuration
PROJECT_NAME="geniotech-crm"
PROJECT_DIR="/var/www/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="geniotech-crm"

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Setting up services for GENIO TECH CRM..."

# Setup PostgreSQL Database
print_status "Configuring PostgreSQL database..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres createdb geniotech_crm
sudo -u postgres createuser geniotech_user

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Gunicorn instance to serve GENIO TECH CRM
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn --workers 4 --bind 0.0.0.0:8002 wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $PROJECT_DIR/static;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Start services
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl restart nginx

print_status "Services setup completed!" 