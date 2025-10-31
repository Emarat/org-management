#!/usr/bin/env python
"""
Helper script for common management tasks
"""
import os
import sys
import subprocess
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*50}")
    print(f"{text}")
    print(f"{'='*50}{Colors.END}\n")

def run_command(cmd, description):
    print(f"{Colors.BLUE}→ {description}...{Colors.END}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode == 0:
        print(f"{Colors.GREEN}✓ Success!{Colors.END}\n")
        return True
    else:
        print(f"{Colors.RED}✗ Failed!{Colors.END}\n")
        return False

def main():
    python_cmd = '"/home/emarat/Org Management/.venv/bin/python"'
    
    print_header("Organization Management System - Helper")
    
    print("What would you like to do?\n")
    print("1. Create Admin User (Superuser)")
    print("2. Start Development Server")
    print("3. Make Migrations")
    print("4. Apply Migrations")
    print("5. Backup Database")
    print("6. Check System")
    print("7. Run Tests")
    print("8. Create Sample Data")
    print("9. Exit")
    
    choice = input("\nEnter your choice (1-9): ").strip()
    
    if choice == '1':
        print_header("Create Admin User")
        run_command(f'{python_cmd} manage.py createsuperuser', "Creating superuser")
    
    elif choice == '2':
        print_header("Starting Development Server")
        print(f"{Colors.GREEN}Server will start at: http://localhost:8000/{Colors.END}")
        print(f"{Colors.YELLOW}Press Ctrl+C to stop the server{Colors.END}\n")
        os.system(f'{python_cmd} manage.py runserver')
    
    elif choice == '3':
        print_header("Making Migrations")
        run_command(f'{python_cmd} manage.py makemigrations', "Creating migration files")
    
    elif choice == '4':
        print_header("Applying Migrations")
        run_command(f'{python_cmd} manage.py migrate', "Applying database migrations")
    
    elif choice == '5':
        print_header("Backup Database")
        backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        if run_command(f'cp db.sqlite3 {backup_name}', f"Creating backup: {backup_name}"):
            print(f"{Colors.GREEN}Backup saved as: {backup_name}{Colors.END}")
    
    elif choice == '6':
        print_header("System Check")
        run_command(f'{python_cmd} manage.py check', "Checking system configuration")
    
    elif choice == '7':
        print_header("Running Tests")
        run_command(f'{python_cmd} manage.py test', "Running test suite")
    
    elif choice == '8':
        print_header("Create Sample Data")
        print(f"{Colors.YELLOW}This feature requires Django shell.{Colors.END}")
        print(f"{Colors.BLUE}Use the admin panel to add sample data manually.{Colors.END}")
    
    elif choice == '9':
        print(f"\n{Colors.GREEN}Goodbye!{Colors.END}\n")
        sys.exit(0)
    
    else:
        print(f"\n{Colors.RED}Invalid choice!{Colors.END}\n")
    
    # Ask if user wants to do something else
    again = input("\nDo something else? (y/n): ").strip().lower()
    if again == 'y':
        main()

if __name__ == '__main__':
    main()
