from django.db import models
from optimization_recs_module.models import RuleAnalysisSession


class FalsePositiveDetection(models.Model):
    rule_id = models.CharField(max_length=50)
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='false_positives')
    false_positive_count = models.IntegerField(default=0)
    legitimate_request_count = models.IntegerField(default=0)
    false_positive_rate = models.FloatField(default=0.0)
    blocked_requests = models.JSONField(default=list)
    request_patterns = models.JSONField(default=dict)
    detection_method = models.CharField(max_length=50, default='manual', choices=[('manual', 'Manual Detection'), ('learning', 'Learning Mode'), ('ai', 'AI Detection')])
    confidence_score = models.FloatField(default=0.0)
    STATUS_CHOICES = [('detected', 'Detected'), ('analyzing', 'Analyzing'), ('whitelisted', 'Whitelisted'), ('resolved', 'Resolved')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'false_positive_detections'
        indexes = [
            models.Index(fields=['rule_id', 'false_positive_rate']),
            models.Index(fields=['status']),
            models.Index(fields=['detection_method']),
        ]
        unique_together = ['rule_id', 'session']

    def __str__(self):
        return f"False Positive: {self.rule_id} ({self.false_positive_count} cases)"


class WhitelistSuggestion(models.Model):
    false_positive = models.ForeignKey(FalsePositiveDetection, on_delete=models.CASCADE, related_name='whitelist_suggestions')
    suggestion_type = models.CharField(max_length=50, choices=[('ip_whitelist', 'IP Address Whitelist'), ('user_agent_whitelist', 'User Agent Whitelist'), ('path_whitelist', 'Path Whitelist'), ('parameter_whitelist', 'Parameter Whitelist'), ('header_whitelist', 'Header Whitelist'), ('custom_pattern', 'Custom Pattern')])
    pattern_description = models.TextField()
    pattern_regex = models.TextField(blank=True, null=True)
    pattern_conditions = models.JSONField(default=dict)
    estimated_false_positive_reduction = models.FloatField(default=0.0)
    security_risk_assessment = models.CharField(max_length=20, default='low', choices=[('low', 'Low Risk'), ('medium', 'Medium Risk'), ('high', 'High Risk')])
    implementation_priority = models.CharField(max_length=20, default='medium', choices=[('low', 'Low Priority'), ('medium', 'Medium Priority'), ('high', 'High Priority')])
    STATUS_CHOICES = [('suggested', 'Suggested'), ('approved', 'Approved'), ('implemented', 'Implemented'), ('rejected', 'Rejected')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='suggested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'whitelist_suggestions'
        indexes = [
            models.Index(fields=['suggestion_type']),
            models.Index(fields=['status']),
            models.Index(fields=['implementation_priority']),
        ]

    def __str__(self):
        return f"Whitelist: {self.suggestion_type} for {self.false_positive.rule_id}"


class LearningModeSession(models.Model):
    name = models.CharField(max_length=255)
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='learning_sessions')
    learning_duration_hours = models.IntegerField(default=24)
    traffic_sample_size = models.IntegerField(default=1000)
    normal_traffic_patterns = models.JSONField(default=dict)
    baseline_metrics = models.JSONField(default=dict)
    anomaly_thresholds = models.JSONField(default=dict)
    STATUS_CHOICES = [('active', 'Active Learning'), ('completed', 'Learning Completed'), ('paused', 'Paused'), ('failed', 'Learning Failed')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    patterns_learned = models.IntegerField(default=0)
    false_positive_predictions = models.IntegerField(default=0)
    accuracy_score = models.FloatField(default=0.0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'learning_mode_sessions'
        indexes = [models.Index(fields=['status']), models.Index(fields=['started_at'])]

    def __str__(self):
        return f"Learning Mode: {self.name} ({self.status})"


class WhitelistExport(models.Model):
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='whitelist_exports')
    export_name = models.CharField(max_length=255, default='waf_whitelist.csv')
    file_path = models.CharField(max_length=500, blank=True, null=True)
    include_patterns = models.JSONField(default=list)
    export_format = models.CharField(max_length=20, default='csv', choices=[('csv', 'CSV Format'), ('json', 'JSON Format'), ('xml', 'XML Format')])
    STATUS_CHOICES = [('pending', 'Pending'), ('generating', 'Generating'), ('completed', 'Completed'), ('failed', 'Failed')]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_patterns = models.IntegerField(default=0)
    file_size_bytes = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'whitelist_exports'
        indexes = [models.Index(fields=['status']), models.Index(fields=['created_at'])]

    def __str__(self):
        return f"Export: {self.export_name} ({self.status})"

