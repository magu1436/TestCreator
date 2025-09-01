from django.contrib import admin

from .models import APICostLog

@admin.register(APICostLog)
class APICostLogAdmin(admin.ModelAdmin):
    list_display = (
        "user", "estimated_cost", "request_id", "api_model", "created_at"
    )
    list_filter = (("created_at", admin.DateFieldListFilter),)
    search_fields = ("api_model", "user__username")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj = ...):
        return False
    
    def get_readonly_fields(self, request, obj = ...):
        return [f.name for f in self.model._meta.fields]