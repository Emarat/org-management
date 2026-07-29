# Quick Reference - Bill Claim System

## URLs

- **Submit Claim:** http://127.0.0.1:8000/claims/submit/
- **My Claims:** http://127.0.0.1:8000/claims/my/
- **All Claims (Manager):** http://127.0.0.1:8000/claims/

## Login Credentials

### Managers (can approve/reject)

- **Username:** super-admin | **Role:** Superuser + Manager
- **Username:** emarat | **Role:** Manager

### Employee (can submit claims)

- **Username:** vimrul | **Role:** Regular employee

## Quick Test Steps

### 1. Test Employee Flow (Login as vimrul)

```
→ Go to: http://127.0.0.1:8000/login/
→ Login as: vimrul
→ Click: "Submit Claim"
→ Fill: Amount=$100, Date=today, Description="Office supplies"
→ Submit
→ Click: "My Claims" to see your claim
```

### 2. Test Manager Flow (Login as super-admin or emarat)

```
→ Go to: http://127.0.0.1:8000/login/
→ Login as: super-admin or emarat
→ Click: "Review Claims"
→ See: All claims from all employees with statistics
→ Click: Green ✓ to approve OR Red ✗ to reject
→ Confirm action
→ Check: "Expenses" page to see auto-created expense (if approved)
```

## Current Test Data

- Claim #1: vimrul - $500.00 - pending
- Claim #2: vimrul - $125.50 - pending

## Server

**Status:** ✅ Running  
**URL:** http://127.0.0.1:8000/

## Features

✅ Submit claims with file attachments  
✅ View own claims with filters  
✅ Manager review dashboard with statistics  
✅ Approve claims (auto-creates Expense)  
✅ Reject claims  
✅ Role-based permissions  
✅ Clean Bootstrap UI

## Files to Review

- `IMPLEMENTATION_SUMMARY.md` - Complete implementation details
- `BILL_CLAIMS_FEATURE.md` - Feature documentation
- `core/models.py` - BillClaim model (line 167+)
- `core/views.py` - Claim views (line 285+)
- `core/urls.py` - Claim URLs
- `templates/core/bill_claim_*.html` - Templates
