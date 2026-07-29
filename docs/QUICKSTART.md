# 🚀 Quick Start Guide

## First Time Setup (One Time Only)

### Step 1: Create Admin Account

Run this command to create your login credentials:

```bash
"/home/emarat/Fashion Express/.venv/bin/python" manage.py createsuperuser
```

**Enter:**

- Username: (your choice, e.g., `admin`)
- Email: (optional, press Enter to skip)
- Password: (choose a strong password)

**IMPORTANT: Remember these credentials!**

---

## Starting the Application

### Option 1: Using the Script (Easiest)

```bash
bash start.sh
```

### Option 2: Manual Start

```bash
cd "/home/emarat/Fashion Express"
"/home/emarat/Fashion Express/.venv/bin/python" manage.py runserver
```

---

## Accessing the Application

After starting, open your browser and go to:

### Main Application

```
http://localhost:8000/
```

### Admin Panel (Quick Data Entry)

```
http://localhost:8000/admin/
```

---

## Usage Tips

### ✅ For Beginners: Start with Admin Panel

1. Go to `http://localhost:8000/admin/`
2. Login with your superuser credentials
3. Click on "Employees", "Customers", etc. to add data
4. The admin panel is fastest for bulk data entry!

### ✅ For Better UX: Use the Main Application

1. Go to `http://localhost:8000/`
2. Login with your credentials
3. Nice dashboard with search, filters, and reports

---

## Common Tasks

### Add Sample Data Quickly

1. Login to admin panel: `http://localhost:8000/admin/`
2. Use the "+ Add" buttons to create records

### Export to Excel

1. Go to Reports page in main app
2. Click "Export to Excel"
3. File downloads automatically

### Backup Your Data

Simply copy the `db.sqlite3` file to a safe location!

### Stop the Server

Press `Ctrl + C` in the terminal

---

## Troubleshooting

**Can't login?**
Create a new superuser: `"/home/emarat/Fashion Express/.venv/bin/python" manage.py createsuperuser`

**Port 8000 in use?**
Run on different port: `"/home/emarat/Fashion Express/.venv/bin/python" manage.py runserver 8080`
Then access: `http://localhost:8080/`

---

## What's Included

✅ Employee Management
✅ Customer Management  
✅ Inventory/Warehouse (Machine Parts)
✅ Daily Expenses Tracking
✅ Payment Management (Down Payment, Installments)
✅ Dashboard with Analytics
✅ Excel Export
✅ Search & Filter on all pages
✅ Low Stock Alerts

---

**Need Help? Check the full README.md file!**
