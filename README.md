# Organization Management System

A comprehensive web-based application to manage your organization's operations including employees, customers, inventory, expenses, and payments.

## 🚀 Features

- **Employee Management**: Track employee details, salaries, and status
- **Customer Management**: Manage customer information and relationships
- **Inventory/Warehouse**: Monitor machine parts stock levels with low-stock alerts
- **Daily Expenses**: Record and categorize daily business expenses
- **Payment Tracking**: Manage payments with down payment, installment, and full payment options
- **Dashboard**: Visual overview of key business metrics
- **Reports**: Export data to Excel for further analysis
- **User Authentication**: Secure login system

## 📋 Prerequisites

Before running this application, make sure you have Python installed on your system.

### Check if Python is installed:

```bash
python --version
```

or

```bash
python3 --version
```

If Python is not installed, download it from: https://www.python.org/downloads/

**Minimum Required Version: Python 3.8+**

## 🛠️ Installation & Setup

### Step 1: Install Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

or if you have multiple Python versions:

```bash
pip3 install -r requirements.txt
```

### Step 2: Set Up the Database

Run the following commands to create the database:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Create an Admin User

Create your first admin account:

```bash
python manage.py createsuperuser
```

You'll be prompted to enter:

- Username (choose any username you like)
- Email (optional, press Enter to skip)
- Password (type carefully, it won't be visible)

**Remember these credentials! You'll need them to log in.**

### Step 4: Start the Application

Run the development server:

```bash
python manage.py runserver
```

You should see output like:

```
Starting development server at http://127.0.0.1:8000/
```

## 🌐 Accessing the Application

### Main Application

Open your web browser and go to:

```
http://127.0.0.1:8000/
```

or

```
http://localhost:8000/
```

Log in with the username and password you created in Step 3.

### Django Admin Panel (Optional)

For quick data management, access the built-in admin panel:

```
http://127.0.0.1:8000/admin/
```

## 📱 Using the Application

### Dashboard

- View key metrics and statistics
- See low stock alerts
- Quick access to recent expenses and payments
- Quick action buttons for common tasks

### Employees

- Add, edit, and delete employee records
- Track salaries and employment status
- Search and filter employees

### Customers

- Manage customer information
- Track customer status (active/inactive)
- Search by name, ID, or company

### Inventory

- Add machine parts and track quantities
- Monitor stock levels with automatic low-stock alerts
- Track unit prices and total inventory value
- Search by part name, code, or category

### Expenses

- Record daily expenses by category
- Track payment methods and receipts
- View monthly expense totals
- Filter by category and date

### Payments

- Create payment records linked to customers
- Track down payments, installments, and full payments
- Monitor pending and overdue payments
- Set next payment due dates

### Reports

- View expense breakdowns by category
- Payment statistics
- Export all data to Excel for external analysis

## 🔧 Troubleshooting

### Problem: "Port is already in use"

**Solution**: The default port 8000 is occupied. Run on a different port:

```bash
python manage.py runserver 8080
```

Then access at: `http://localhost:8080/`

### Problem: "Module not found" errors

**Solution**: Reinstall requirements:

```bash
pip install -r requirements.txt --upgrade
```

### Problem: "Database is locked"

**Solution**: Close all other instances of the application and restart.

### Problem: Forgot admin password

**Solution**: Create a new superuser:

```bash
python manage.py createsuperuser
```

### Problem: Changes not appearing

**Solution**:

1. Stop the server (Ctrl+C)
2. Run migrations: `python manage.py migrate`
3. Start server again: `python manage.py runserver`

## 📊 Exporting Data

To export all your data to Excel:

1. Go to the Reports page
2. Click "Export to Excel"
3. The file will download automatically

## 🔐 Security Notes

**For Production Use:**

1. Change the SECRET_KEY in `org_management/settings.py`
2. Set DEBUG = False
3. Update ALLOWED_HOSTS with your domain
4. Use a proper database (PostgreSQL/MySQL instead of SQLite)
5. Set up HTTPS
6. Use environment variables for sensitive data

## 💾 Backup Your Data

**Important**: Your data is stored in `db.sqlite3` file. To backup:

1. Stop the server
2. Copy the `db.sqlite3` file to a safe location
3. Also backup the `media` folder if you store files

To restore:

1. Stop the server
2. Replace `db.sqlite3` with your backup
3. Start the server again

## 🎨 Customization

### Change Company Name

Edit `templates/base.html` and `templates/core/login.html` to update:

- "Organization Management System" to your company name
- Logo and branding

### Add More Categories

Edit `core/models.py` to add categories to:

- Expense categories
- Inventory units
- Custom fields

After editing, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

## 📞 Support

For issues or questions:

1. Check the Troubleshooting section above
2. Review Django documentation: https://docs.djangoproject.com/
3. Check if all dependencies are installed correctly

## 📝 License

This project is for internal business use. Modify as needed for your organization.

## 🔄 Updating the Application

1. Backup your database (copy `db.sqlite3`)
2. Pull/download new code
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Restart the server

---

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver

# Access application
# Open browser: http://localhost:8000/
```

---

**Made with ❤️ for efficient organization management**
