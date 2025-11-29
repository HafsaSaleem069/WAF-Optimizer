from django.contrib import admin
from .models import ThresholdSuggestion

@admin.register(ThresholdSuggestion)
class ThresholdSuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "value", "approved", "applied", "created_at")
    list_filter = ("approved", "applied", "created_at")
    search_fields = ("value",)
    actions = ["approve_selected"]

    def approve_selected(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} suggestion(s) approved.")
    approve_selected.short_description = "Approve selected suggestions"
