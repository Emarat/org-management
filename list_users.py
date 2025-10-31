from accounts.models import CustomUser

# List all users
users = CustomUser.objects.all()
if users.exists():
    print("All users:")
    for user in users:
        print(f"  - {user.username} (is_manager: {user.is_manager}, is_superuser: {user.is_superuser})")
else:
    print("No users found")
