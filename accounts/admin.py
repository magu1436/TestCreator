from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AdminUser


@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("権限情報", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("その他", {"fields": ("date_joined",)}),
    )
    add_fieldsets = (
        (None, {
            "classed": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
    )
    list_display = ("username", "is_staff", "is_active", "date_joined")
    ordering = ("username",)
    filter_horizontal = ()
    search_fields = ("username",)