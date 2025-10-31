# 📁 Project Structure Explained

## Complete File Tree

```
Org Management/
│
├── 📄 START_HERE.md              ← START HERE! Quick start guide
├── 📄 QUICKSTART.md              ← Fast setup instructions
├── 📄 README.md                  ← Complete documentation
├── 📄 USER_GUIDE.md              ← How to use each feature
├── 📄 GETTING_STARTED.md         ← Comprehensive guide
│
├── 📄 manage.py                  ← Django management tool
├── 📄 requirements.txt           ← Python dependencies
├── 📄 helper.py                  ← Interactive helper script
├── 📄 start.sh                   ← Linux/Mac startup script
├── 📄 start.bat                  ← Windows startup script
├── 📄 .gitignore                 ← Git ignore file
│
├── 💾 db.sqlite3                 ← YOUR DATABASE (backup this!)
│
├── 📁 .venv/                     ← Python virtual environment
│   └── (Python packages installed here)
│
├── 📁 org_management/            ← Django project settings
│   ├── __init__.py
│   ├── settings.py               ← Main configuration
│   ├── urls.py                   ← URL routing
│   ├── wsgi.py                   ← WSGI config
│   └── asgi.py                   ← ASGI config
│
├── 📁 core/                      ← Main application
│   ├── __init__.py
│   ├── apps.py                   ← App configuration
│   ├── models.py                 ← Database models (IMPORTANT!)
│   ├── views.py                  ← Business logic
│   ├── forms.py                  ← Form definitions
│   ├── admin.py                  ← Admin panel config
│   ├── urls.py                   ← URL patterns
│   │
│   └── 📁 migrations/            ← Database migrations
│       ├── __init__.py
│       └── 0001_initial.py       ← Initial database structure
│
├── 📁 templates/                 ← HTML templates
│   ├── base.html                 ← Main layout template
│   │
│   └── 📁 core/                  ← Feature templates
│       ├── login.html            ← Login page
│       ├── dashboard.html        ← Dashboard
│       ├── employee_list.html    ← Employee list
│       ├── employee_form.html    ← Add/Edit employee
│       ├── customer_list.html    ← Customer list
│       ├── customer_form.html    ← Add/Edit customer
│       ├── inventory_list.html   ← Inventory list
│       ├── inventory_form.html   ← Add/Edit inventory
│       ├── expense_list.html     ← Expense list
│       ├── expense_form.html     ← Add/Edit expense
│       ├── payment_list.html     ← Payment list
│       ├── payment_form.html     ← Add/Edit payment
│       ├── reports.html          ← Reports page
│       └── confirm_delete.html   ← Delete confirmation
│
├── 📁 static/                    ← Static files (CSS, JS, images)
│   └── style.css                 ← Custom styles
│
└── 📁 media/                     ← User uploaded files (future use)
```

---

## 🔍 What Each File Does

### Documentation Files (📄)

| File                   | Purpose                          | When to Read        |
| ---------------------- | -------------------------------- | ------------------- |
| **START_HERE.md**      | First steps after installation   | Right now!          |
| **QUICKSTART.md**      | Fast 5-minute setup              | When starting fresh |
| **README.md**          | Complete guide & troubleshooting | For detailed info   |
| **USER_GUIDE.md**      | Feature-by-feature instructions  | When using features |
| **GETTING_STARTED.md** | Comprehensive overview           | For understanding   |

### Core Application Files

#### Django Project (`org_management/`)

- **settings.py** - Database, apps, security settings
- **urls.py** - Main URL routing
- **wsgi.py** / **asgi.py** - Server deployment configs

#### Main App (`core/`)

- **models.py** - Defines data structure (Employee, Customer, etc.)
- **views.py** - Handles requests and responses
- **forms.py** - Form validations and styling
- **admin.py** - Admin panel configuration
- **urls.py** - URL patterns for features

#### Templates (`templates/`)

- **base.html** - Main layout (sidebar, navbar)
- **core/\*.html** - Individual pages for each feature

#### Static Files (`static/`)

- CSS, JavaScript, images
- Currently using CDN for Bootstrap & Font Awesome

---

## 🎯 Important Files to Know

### 💾 Database

```
db.sqlite3
```

**This is your data!** Backup regularly!

### ⚙️ Configuration

```
org_management/settings.py
```

Change settings like timezone, language, security

### 📊 Data Models

```
core/models.py
```

Modify to add/remove fields or tables

### 🎨 Design

```
templates/base.html
static/style.css
```

Edit to customize look and feel

---

## 🔧 Files You Might Edit

### Beginners (No Coding)

Just use the web interface! No file editing needed.

### Basic Customization

1. **templates/base.html** - Change company name, logo
2. **static/style.css** - Change colors
3. **templates/core/login.html** - Customize login page

### Advanced Customization

1. **core/models.py** - Add fields/tables
2. **core/forms.py** - Modify forms
3. **core/views.py** - Change business logic
4. **templates/core/\*.html** - Modify pages

---

## 🚫 Files NOT to Touch

- `migrations/` - Auto-generated, don't edit!
- `.venv/` - Python environment, managed automatically
- `__pycache__/` - Python cache, auto-generated
- `manage.py` - Django tool, don't modify

---

## 📂 Where is Everything?

### Where is my data?

```
db.sqlite3
```

### Where are the web pages?

```
templates/core/
```

### Where are the forms defined?

```
core/forms.py
```

### Where is the business logic?

```
core/views.py
```

### Where is the database structure?

```
core/models.py
core/migrations/
```

### Where are the URL routes?

```
org_management/urls.py  (main)
core/urls.py            (features)
```

---

## 🔄 Workflow: How It All Works

```
1. User visits URL
   ↓
2. urls.py routes to correct view
   ↓
3. views.py processes request
   ↓
4. models.py interacts with database
   ↓
5. forms.py validates input (if form)
   ↓
6. templates/*.html displays result
   ↓
7. Browser shows page to user
```

---

## 📦 What Gets Created When You Run

### First Time Setup

```bash
python manage.py migrate
```

Creates:

- db.sqlite3
- All database tables

### When You Add Data

Data stored in:

- db.sqlite3 (database file)

### When You Export

Creates:

- Excel file in your Downloads folder

---

## 🎓 Understanding the Structure

### Django App Pattern (MVT)

- **M**odels (models.py) - Data structure
- **V**iews (views.py) - Business logic
- **T**emplates (templates/) - User interface

### Your App Structure

```
Models (Database)
  ↓
Views (Logic)
  ↓
Templates (Display)
```

---

## 💡 Quick Tips

### Want to add a field to Employee?

Edit: `core/models.py` → Run migrations

### Want to change dashboard?

Edit: `templates/core/dashboard.html`

### Want to add new category?

Edit: `core/models.py` (CATEGORY_CHOICES)

### Want different colors?

Edit: `templates/base.html` (CSS section)

### Want to add new page?

1. Add URL in `core/urls.py`
2. Add view in `core/views.py`
3. Create template in `templates/core/`

---

## 🔍 Searching the Code

### Find where "Employee" is defined:

Look in: `core/models.py`

### Find employee list page:

Look in: `templates/core/employee_list.html`

### Find how employee form works:

Look in: `core/forms.py` (form definition)
Look in: `core/views.py` (form handling)
Look in: `templates/core/employee_form.html` (display)

---

## 📚 Learning Path

1. **Week 1**: Just use the web interface
2. **Week 2**: Read templates to understand pages
3. **Week 3**: Modify templates for customization
4. **Week 4**: Add fields using models.py
5. **Week 5**: Create custom views/pages

---

## 🎯 Most Useful Files for Beginners

1. **START_HERE.md** - Start here!
2. **USER_GUIDE.md** - How to use features
3. **templates/base.html** - Change company name/branding
4. **db.sqlite3** - Your actual data (backup this!)

---

**Understanding the structure helps you customize the app for your needs!** 🚀
