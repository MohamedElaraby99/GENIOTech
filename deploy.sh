#!/bin/bash
# Deployment script for GENIO TECH CRM

set -e  # Exit on any error

echo "🚀 Starting GENIO TECH CRM Deployment..."

# Configuration
PROJECT_NAME="geniotech-crm"
PROJECT_DIR="/var/www/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="geniotech-crm"
NGINX_AVAILABLE="/etc/nginx/sites-available/$PROJECT_NAME"
NGINX_ENABLED="/etc/nginx/sites-enabled/$PROJECT_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git curl

# Create project directory
print_status "Creating project directory..."
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Clone or update repository
if [ -d "$PROJECT_DIR/.git" ]; then
    print_status "Updating existing repository..."
    cd $PROJECT_DIR
    git pull origin main
else
    print_status "Cloning repository..."
    # Replace with your actual repository URL
    # git clone https://github.com/yourusername/geniotech-crm.git $PROJECT_DIR
    # For now, copy current directory
    cp -r . $PROJECT_DIR/
    cd $PROJECT_DIR
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv $VENV_DIR

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_status "Creating environment configuration..."
    cat > $PROJECT_DIR/.env << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=sqlite:///instance/crm.db

# Application Settings
APP_NAME=GENIO TECH CRM
HOST=0.0.0.0
PORT=8002
WORKERS=4

# Security Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
EOF
    print_warning "Environment file created. Please review and update $PROJECT_DIR/.env"
fi

# Create instance directory
mkdir -p $PROJECT_DIR/instance
mkdir -p $PROJECT_DIR/temp
mkdir -p $PROJECT_DIR/logs

# Set proper permissions
sudo chown -R $USER:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR
sudo chmod -R 775 $PROJECT_DIR/instance
sudo chmod -R 775 $PROJECT_DIR/temp
sudo chmod -R 775 $PROJECT_DIR/logs

print_status "✅ Basic deployment setup completed!"
print_warning "Please run 'sudo ./setup_services.sh' to configure database, nginx, and systemd services." 