from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # (1) Control what shows in the list view
    list_display = ["username", "email", "is_staff", "is_online"]

    # (2) Control what shows in the search and filter sidebars
    search_fields = ["username", "email"]
    list_filter = ["is_staff", "is_online"]

    # (3) Adjust the detail view fields (this hides the password hash)
    # This keeps the default "User" fields but allows you to add your custom fields
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Status Info", {"fields": ("is_online", "profile_picture")}),
    )

    # (4) This handles the "Add User" form specifically
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Extra Info", {"fields": ("email", "is_online")}),
    )
