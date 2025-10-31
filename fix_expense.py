from core.models import Expense, BillClaim

print("Fixing existing expense with empty 'Paid to' field...")

# Get the expense
expense = Expense.objects.get(id=1)
print(f"Expense #1: Paid to = '{expense.paid_to}'")

# Get the related claim
claim = BillClaim.objects.get(expense=expense)
print(f"Related Claim #1: Submitter = {claim.submitter.username}")

# Fix the paid_to field
employee_name = claim.submitter.get_full_name().strip()
if not employee_name:
    employee_name = claim.submitter.username

expense.paid_to = employee_name
expense.description = f"Bill Claim by {employee_name}: {claim.description}"
expense.save()

print(f"✅ Fixed! Paid to = '{expense.paid_to}'")
print(f"✅ Description updated: {expense.description[:50]}...")
