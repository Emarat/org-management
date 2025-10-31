from accounts.models import CustomUser
from core.models import BillClaim
from decimal import Decimal
from datetime import date

print("=" * 60)
print("BILL CLAIM SYSTEM TEST")
print("=" * 60)

# Test 1: Check users
print("\n1. Checking Users:")
users = CustomUser.objects.all()
for user in users:
    print(f"   - {user.username}: manager={user.is_manager}, superuser={user.is_superuser}")

# Test 2: Create a test claim
print("\n2. Creating Test Claim:")
try:
    employee = CustomUser.objects.get(username='vimrul')
    claim = BillClaim.objects.create(
        submitter=employee,
        amount=Decimal('125.50'),
        description='Office supplies purchase - printer paper and toner',
        bill_date=date.today(),
        status='pending'
    )
    print(f"   ✅ Created claim #{claim.id} for ${claim.amount}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check all claims
print("\n3. All Bill Claims:")
claims = BillClaim.objects.all()
if claims.exists():
    for claim in claims:
        print(f"   Claim #{claim.id}: {claim.submitter.username} - ${claim.amount} - {claim.status}")
else:
    print("   No claims found")

# Test 4: Check managers
print("\n4. Managers:")
managers = CustomUser.objects.filter(is_manager=True)
for mgr in managers:
    print(f"   - {mgr.username} ({mgr.get_full_name()})")

print("\n" + "=" * 60)
print("TEST COMPLETED!")
print("=" * 60)
