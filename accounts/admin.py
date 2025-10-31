from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'employee_id', 'first_name', 'last_name', 'is_staff', 'is_manager', 'status')
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {'fields': ('position', 'department', 'phone', 'address', 'salary', 'join_date', 'status', 'notes', 'is_manager')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {'fields': ('position', 'department', 'phone', 'address', 'salary', 'join_date', 'status', 'notes', 'is_manager')}),
    )
    readonly_fields = ('employee_id',)
    search_fields = ('username', 'employee_id', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'status', 'department', 'is_manager')