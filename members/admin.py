"""Django's built-in admin (/django-admin/): a back door for the owner, not the friendly Admin page."""
from django.contrib import admin

from .models import Invite, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_admin", "is_active", "date_joined"]
    list_filter = ["is_admin", "is_active"]
    search_fields = ["name", "email"]
    exclude = ["password", "groups", "user_permissions"]


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "used_at", "used_by", "cancelled_at"]
    readonly_fields = ["token", "created_at"]
