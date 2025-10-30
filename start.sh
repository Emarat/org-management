#!/bin/bash

echo "======================================"
echo "Organization Management System"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Check if superuser exists
echo ""
echo "======================================"
echo "Do you want to create an admin user?"
echo "======================================"
read -p "(y/n): " create_user

if [ "$create_user" = "y" ] || [ "$create_user" = "Y" ]; then
    python manage.py createsuperuser
fi

# Start server
echo ""
echo "======================================"
echo "Starting Organization Management System..."
echo "======================================"
echo "Access the application at: http://localhost:8000/"
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver
