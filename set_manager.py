from accounts.models import CustomUser

# Set super-admin as manager
try:
    user = CustomUser.objects.get(username='super-admin')
    user.is_manager = True
    user.save()
    print(f"✅ User '{user.username}' is now a manager")
except CustomUser.DoesNotExist:
    print("❌ super-admin user not found")

# Also set emarat as manager
try:
    user = CustomUser.objects.get(username='emarat')
    user.is_manager = True
    user.save()
    print(f"✅ User '{user.username}' is now a manager")
except CustomUser.DoesNotExist:
    print("❌ emarat user not found")
