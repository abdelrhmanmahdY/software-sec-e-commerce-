from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only: nobody, including superusers, edits or deletes audit rows here."""

    list_display = ("timestamp", "action", "username", "ip_address", "object_type", "object_repr", "path")
    list_filter = ("action", "timestamp")
    search_fields = ("username", "ip_address", "object_repr", "path")
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
