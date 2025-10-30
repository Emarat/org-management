# 📖 User Guide - Organization Management System

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Employees](#managing-employees)
3. [Managing Customers](#managing-customers)
4. [Inventory Management](#inventory-management)
5. [Expense Tracking](#expense-tracking)
6. [Payment Management](#payment-management)
7. [Reports & Export](#reports--export)
8. [Tips & Tricks](#tips--tricks)

---

## Getting Started

### First Login

1. Make sure the server is running (`./start.sh` or `python manage.py runserver`)
2. Open browser: http://localhost:8000/
3. Login with your superuser credentials

### Dashboard Overview

The dashboard shows:

- **Active Employees & Customers**: Current count
- **Inventory Items**: Total items and low stock alerts
- **Pending Payments**: Amount awaiting collection
- **Monthly Expenses**: Current month total
- **Recent Activity**: Last 5 expenses and payments
- **Low Stock Alerts**: Items needing restocking

---

## Managing Employees

### Adding an Employee

1. Click "Employees" in sidebar
2. Click "Add New Employee" button
3. Fill in required fields:
   - **Name**: Full name
   - **Employee ID**: Unique identifier (e.g., EMP001)
   - **Position**: Job title
   - **Phone**: Contact number
   - **Salary**: Monthly/Annual salary
   - **Join Date**: Employment start date
   - **Status**: Active/Inactive/On Leave

### Searching Employees

- Use search box to find by name, ID, position, or department
- Filter by status (Active/Inactive/On Leave)

### Editing/Deleting

- Click edit icon (✏️) to modify
- Click delete icon (🗑️) to remove (confirmation required)

---

## Managing Customers

### Adding a Customer

1. Go to "Customers" section
2. Click "Add New Customer"
3. Fill in:
   - **Name**: Customer name
   - **Customer ID**: Unique ID (e.g., CUST001)
   - **Company**: Company name (optional)
   - **Phone**: Contact number
   - **Email**: Email address (optional)
   - **City**: Location
   - **Status**: Active/Inactive

### Linking to Payments

- Customer IDs are used when creating payment records
- View all customer payments from payment list

---

## Inventory Management

### Adding Machine Parts

1. Navigate to "Inventory"
2. Click "Add New Item"
3. Enter:
   - **Part Name**: Description of part
   - **Part Code**: Unique code (e.g., PART001)
   - **Category**: Type/category (optional)
   - **Quantity**: Current stock
   - **Unit**: Pieces/Box/Kg/Liter/Meter
   - **Unit Price**: Price per unit
   - **Location**: Warehouse location/shelf
   - **Minimum Stock**: Alert threshold

### Low Stock Alerts

- Items below minimum stock show in dashboard
- Highlighted in yellow in inventory list
- Filter to see only low stock items

### Stock Management

- Edit item to update quantity
- Stock history is automatically tracked
- Total inventory value calculated automatically

---

## Expense Tracking

### Recording Expenses

1. Go to "Expenses"
2. Click "Add New Expense"
3. Fill in:
   - **Date**: Expense date
   - **Category**: Salary/Utilities/Maintenance/Transport/Supplies/Rent/Marketing/Other
   - **Description**: What was purchased/paid for
   - **Amount**: Cost
   - **Paid To**: Vendor/recipient
   - **Payment Method**: Cash/Bank Transfer/etc.
   - **Receipt Number**: For tracking (optional)

### Viewing Expenses

- Filter by category
- Filter by month
- Search by description or vendor
- Total expenses shown at top

### Monthly Reports

- Use month filter to see specific period
- Export to Excel for detailed analysis

---

## Payment Management

### Understanding Payment Types

**Down Payment**

- Initial payment from customer
- Set next payment date for remaining amount
- Status: Pending

**Installment**

- Partial payments over time
- Track multiple installments per invoice
- Update paid amount as customer pays

**Full Payment**

- Complete payment received
- Mark status as Completed

### Adding a Payment

1. Go to "Payments"
2. Click "Add New Payment"
3. Fill in:
   - **Customer**: Select from dropdown
   - **Invoice Number**: Unique invoice ID
   - **Payment Type**: Down Payment/Installment/Full Payment
   - **Total Amount**: Total invoice amount
   - **Paid Amount**: Amount received so far
   - **Payment Date**: When payment received
   - **Next Payment Date**: When next installment due (if applicable)
   - **Status**: Pending/Completed/Overdue/Cancelled

### Tracking Payments

- **Remaining Amount**: Auto-calculated (Total - Paid)
- **Status Colors**:
  - 🟢 Green = Completed
  - 🟡 Yellow = Pending
  - 🔴 Red = Overdue

### Payment Reminders

- Check "Next Payment Date" column
- Filter by status to see overdue payments
- Dashboard shows pending payment totals

---

## Reports & Export

### Available Reports

1. **Expense Breakdown**: By category for current year
2. **Payment Statistics**: Pending/Completed/Overdue counts
3. **Dashboard Analytics**: Real-time metrics

### Exporting to Excel

1. Go to "Reports" page
2. Click "Export All Data to Excel"
3. File downloads with all data in separate sheets:
   - Employees
   - Customers
   - Inventory
   - Expenses
   - Payments

### Using Exported Data

- Open in Microsoft Excel, LibreOffice, or Google Sheets
- Create pivot tables for analysis
- Share with accountants
- Archive for records

---

## Tips & Tricks

### For Faster Data Entry

- Use the Admin Panel (http://localhost:8000/admin/)
- Admin interface is simpler for bulk entry
- Main app is better for day-to-day use

### Unique IDs

- Use consistent format (EMP001, CUST001, INV-2024-001)
- Makes searching easier
- Professional appearance

### Regular Backups

- Copy `db.sqlite3` file weekly
- Store in cloud (Dropbox, Google Drive)
- Keep 3-4 recent backups

### Categories & Organization

**Expenses:**

- Be consistent with categories
- Use notes field for details
- Keep receipts physically or scan

**Inventory:**

- Use location field (Shelf A1, Bin 23, etc.)
- Set realistic minimum stock levels
- Review low stock weekly

**Payments:**

- Use clear invoice numbering (INV-2024-001)
- Update paid amount when customer pays
- Set next payment date reminders

### Search Tips

- Search works on multiple fields
- Use partial terms (searching "john" finds "Johnson")
- Combine search with filters for best results

### Security

- Don't share admin password
- Create separate users for team members (Django admin can do this)
- Logout when done on shared computers

### Performance

- Database handles thousands of records easily
- Export old records yearly and archive
- For very large operations (10,000+ records), consider upgrading to PostgreSQL

---

## Keyboard Shortcuts

- **Ctrl + S**: Save forms (when in form fields)
- **Ctrl + F**: Browser search on list pages
- **Esc**: Close modal dialogs (if any)

---

## Common Workflows

### Weekly Tasks

1. Check low stock alerts
2. Review pending payments
3. Add new expenses
4. Update payment statuses

### Monthly Tasks

1. Export data to Excel
2. Backup database
3. Review expense breakdown
4. Check overdue payments

### When Customer Pays

1. Go to Payments
2. Find invoice
3. Click edit
4. Update "Paid Amount"
5. If fully paid, change status to "Completed"

### When Stock Arrives

1. Go to Inventory
2. Find part
3. Click edit
4. Update quantity
5. Stock history automatically tracked

---

## Getting Help

### Common Questions

**Q: Can I customize categories?**
A: Yes! Edit `core/models.py` and add to CATEGORY_CHOICES. Then run migrations.

**Q: Can multiple users access simultaneously?**
A: Yes! Just make sure server is running and accessible on your network.

**Q: How to add more fields?**
A: Edit models in `core/models.py`, forms in `core/forms.py`, and templates.

**Q: Mobile access?**
A: Yes! Interface is responsive. Access via phone browser (use your computer's IP).

**Q: Forgot password?**
A: Run `python manage.py createsuperuser` to create new admin account.

---

## Best Practices

1. ✅ Enter data daily, not weekly
2. ✅ Use consistent naming/numbering
3. ✅ Backup weekly
4. ✅ Review reports monthly
5. ✅ Update payment statuses promptly
6. ✅ Set realistic stock minimums
7. ✅ Keep notes field updated
8. ✅ Export data for tax season

---

**Made your Excel data management easy! 🎉**
