from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['actor', 'action', 'resource_type',
                     'resource_id', 'ip_address', 'timestamp']
    list_filter   = ['action', 'resource_type']
    search_fields = ['actor__email', 'resource_type']
    ordering      = ['-timestamp']
    readonly_fields = ['actor', 'action', 'resource_type',
                       'resource_id', 'metadata', 'timestamp']