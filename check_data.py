from core.models import BillClaim, Expense

print("=" * 60)
print("CHECKING EXISTING DATA")
print("=" * 60)

# Check claims
print("\nBill Claims:")
claims = BillClaim.objects.all()
for claim in claims:
    print(f"  Claim #{claim.id}: {claim.submitter.username} - ${claim.amount} - {claim.status}")
    if claim.expense:
        print(f"    → Linked to Expense #{claim.expense.id}")

# Check expenses
print("\nExpenses:")
expenses = Expense.objects.all()
for expense in expenses:
    print(f"  Expense #{expense.id}: ${expense.amount} - Paid to: '{expense.paid_to}'")
    print(f"    Description: {expense.description[:50]}...")
    
    # Check if linked to claim
    try:
        claim = BillClaim.objects.get(expense=expense)
        print(f"    → Linked to Claim #{claim.id}")
    except BillClaim.DoesNotExist:
        print(f"    → Not linked to any claim")

print("\n" + "=" * 60)
