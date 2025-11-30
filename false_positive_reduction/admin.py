from django.contrib import admin
from .models import FalsePositiveDetection, WhitelistSuggestion, LearningModeSession, WhitelistExport


@admin.register(FalsePositiveDetection)
class FalsePositiveDetectionAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'session', 'false_positive_rate', 'status', 'detection_method', 'updated_at')
    list_filter = ('status', 'detection_method')
    search_fields = ('rule_id',)


@admin.register(WhitelistSuggestion)
class WhitelistSuggestionAdmin(admin.ModelAdmin):
    list_display = ('false_positive', 'suggestion_type', 'status', 'estimated_false_positive_reduction')
    list_filter = ('suggestion_type', 'status')


@admin.register(LearningModeSession)
class LearningModeSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'status', 'patterns_learned', 'accuracy_score')
    list_filter = ('status',)


@admin.register(WhitelistExport)
class WhitelistExportAdmin(admin.ModelAdmin):
    list_display = ('export_name', 'session', 'status', 'total_patterns', 'file_size_bytes')
    list_filter = ('status',)

