#!/bin/bash
# SSL Setup script for GENIO TECH CRM using Let's Encrypt

set -e

PROJECT_NAME="geniotech-crm"

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

if [ -z "$1" ]; then
    echo "Usage: $0 <domain-name>"
    echo "Example: $0 geniotech.example.com"
    exit 1
fi

DOMAIN=$1

print_status "Setting up SSL certificate for $DOMAIN..."

# Install Certbot
print_status "Installing Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
print_status "Obtaining SSL certificate..."
certbot --nginx -d $DOMAIN --agree-tos --no-eff-email --redirect

# Update Nginx configuration for better security
print_status "Updating Nginx configuration for security..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/$PROJECT_NAME/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload limit
    client_max_body_size 16M;
}
EOF

# Test and reload Nginx
nginx -t
systemctl reload nginx

# Setup automatic renewal
print_status "Setting up automatic certificate renewal..."
crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | crontab -

print_status "✅ SSL setup completed!"
echo "Your site is now available at: https://$DOMAIN" 