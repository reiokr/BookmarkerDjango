from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    readonly_fields = ['date_joined', 'date_updated',
                       'last_login', "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("password",)}),
        ("Personal info", {"fields": ("first_name", "last_name", "email",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "first_name", "last_name", "is_staff",)
    list_filter = ("is_staff", "is_superuser", "is_active", "groups",)
    search_fields = ("first_name", "last_name", "email",)
    ordering = ("email",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    # ('Personal info', {
    #     'fields': ('first_name', 'last_name', 'email')
    # }),
    # ('Permissions', {
    #     'fields': (
    #         'is_active', 'is_staff', 'is_superuser',
    #         'groups', 'user_permissions'
    #     )
    # }),
    # ('Important dates', {
    #     'fields': ('last_login', 'date_joined')
    # }),
    # ('Additional info', {
    #     'fields': ('is_student', 'is_teacher', 'mailing_address')
    # })


admin.site.register(CustomUser, CustomUserAdmin)
