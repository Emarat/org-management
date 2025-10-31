# Bill Claim Management Feature

## Overview

The Bill Claim Management feature allows employees to submit expense claims/bills for reimbursement, and managers to review and approve or reject these claims.

## Features Implemented

### 1. Employee Features

- **Submit Bill Claim**: Employees can submit new bill claims with:
  - Amount (required)
  - Bill date (required)
  - Description (required)
  - Attachment (optional - upload scanned bill/receipt)
- **View My Claims**: Employees can:
  - View all their submitted claims
  - Filter by status (pending/approved/rejected)
  - See claim status and details
  - Download uploaded attachments

### 2. Manager Features

- **Review All Claims**: Managers can:
  - View all claims from all employees
  - See comprehensive statistics (total pending, approved, rejected amounts)
  - Filter by status
  - Search by employee name or description
- **Approve Claims**: Managers can:
  - Review claim details
  - Approve claims
  - Automatically creates an Expense record when approved
- **Reject Claims**: Managers can:
  - Review claim details
  - Reject claims with proper tracking

## Technical Implementation

### Models

- **BillClaim Model** (`core/models.py`):
  - submitter: Link to User (employee)
  - amount: Decimal field
  - description: Text field
  - bill_date: Date field
  - status: Choice field (pending/approved/rejected)
  - attachment: File field for bill uploads
  - approved_by: Link to approving manager
  - approval_date: Date field
  - expense: Link to created Expense when approved
  - created_at, updated_at: Timestamps

### Views

- **submit_bill_claim**: Employee submits new claim
- **my_bill_claims**: Employee views their claims
- **list_bill_claims**: Manager views all claims (requires @manager_required)
- **approve_bill_claim**: Manager approves claim (requires @manager_required)
- **reject_bill_claim**: Manager rejects claim (requires @manager_required)

### URLs

- `/claims/submit/` - Submit new claim
- `/claims/my/` - View my claims
- `/claims/` - Manager: View all claims
- `/claims/<id>/approve/` - Manager: Approve claim
- `/claims/<id>/reject/` - Manager: Reject claim

### Templates

- `bill_claim_form.html` - Form to submit new claim
- `bill_claim_list.html` - List of claims (used by both employees and managers)
- `bill_claim_review.html` - Review page for approve/reject

### Navigation

- **Submit Claim** - Available to all authenticated users
- **My Claims** - Available to all authenticated users
- **Review Claims** - Available only to managers and superusers

## User Roles

### Manager Role

- Users with `is_manager=True` OR `is_superuser=True` can access manager features
- Current managers:
  - super-admin (superuser + manager)
  - emarat (manager)

### Regular Employee

- User: vimrul (can submit and view own claims)

## Database Migrations

All migrations have been applied:

- ✅ BillClaim model created
- ✅ Database tables created
- ✅ File upload directory configured (media/bill_attachments/)

## File Uploads

- Bills/receipts are uploaded to: `media/bill_attachments/`
- Supported formats: All standard file types
- Files are served in development mode via Django's static file serving

## Workflow

### Employee Workflow

1. Click "Submit Claim" in navigation
2. Fill out form (amount, date, description, upload bill)
3. Submit claim
4. View status in "My Claims"
5. See approval/rejection status and details

### Manager Workflow

1. Click "Review Claims" in navigation
2. View all pending claims from all employees
3. Click approve (✓) or reject (✗) button
4. Review claim details
5. Confirm approval or rejection
6. When approved:
   - Claim status changes to "approved"
   - Expense record is automatically created
   - Employee gets paid back

## Automatic Expense Creation

When a claim is approved:

- Category: "other"
- Description: "Bill Claim by [Employee Name]: [Description]"
- Amount: Same as claim amount
- Paid To: Employee's full name
- Payment Method: "bank_transfer"
- Notes: "Approved bill claim (ID: [claim_id])"

## Testing the Feature

### As Employee:

1. Login as `vimrul` (or any non-manager user)
2. Go to "Submit Claim"
3. Fill out the form and submit
4. Go to "My Claims" to see submitted claims
5. Note: "Review Claims" link should NOT appear for regular employees

### As Manager:

1. Login as `super-admin` or `emarat`
2. Go to "Review Claims"
3. See all claims from all employees
4. Click approve or reject buttons
5. Confirm action
6. Check "Expenses" to see auto-created expense records for approved claims

## Server Status

✅ Server is running at: http://127.0.0.1:8000/

## Pages Available

- ✅ http://127.0.0.1:8000/claims/submit/ - Submit new claim
- ✅ http://127.0.0.1:8000/claims/my/ - My claims
- ✅ http://127.0.0.1:8000/claims/ - All claims (manager only)

## Next Steps (Optional Enhancements)

1. Email notifications when claims are approved/rejected
2. Comments/feedback on rejected claims
3. Multi-level approval workflow
4. Claim categories (travel, meals, supplies, etc.)
5. Monthly claim limits per employee
6. Export claims to Excel
7. Approval history tracking
8. Bulk approve/reject functionality
