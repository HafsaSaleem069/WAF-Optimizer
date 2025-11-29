# rule_analysis/models.py - COMPLETE VERSION WITH ALL MODELS
from django.db import models
from data_management.models import UploadedFile

"""
class RuleAnalysisSession(models.Model):
    ANALYSIS_TYPES = [
        ('SHD', 'Shadowing'),
        ('GEN', 'Generalization'),
        ('RXD', 'Redundancy X'),
        ('RYD', 'Redundancy Y'),
        ('COR', 'Correlation'),
    ]
    
    name = models.CharField(max_length=255)
    rules_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, null=True, blank=True, related_name='rules_analyses')
    traffic_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE,  null=True, blank=True, related_name='traffic_analyses')
    analysis_types = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    results = models.JSONField(null=True, blank=True)
    ai_available = models.BooleanField(default=False)
    ai_processed = models.BooleanField(default=False)
    ai_error = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class RuleRelationship(models.Model):
    RELATIONSHIP_TYPES = [
        ('SHD', 'Shadowing - Rule A shadows Rule B'),
        ('GEN', 'Generalization - Rule A is more general than Rule B'),
        ('RXD', 'Redundancy X - Rules trigger on identical patterns'),
        ('RYD', 'Redundancy Y - Rules are functionally equivalent'),
        ('COR', 'Correlation - Rules frequently trigger together'),
    ]
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='relationships')
    relationship_type = models.CharField(max_length=3, choices=RELATIONSHIP_TYPES)
    rule_a = models.CharField(max_length=50)
    rule_b = models.CharField(max_length=50)
    confidence = models.FloatField()
    evidence_count = models.IntegerField(default=0)
    conflicting_fields = models.JSONField()
    description = models.TextField()
    ai_suggestion = models.JSONField(null=True, blank=True)
    ai_action = models.CharField(max_length=50, blank=True, null=True)
    ai_optimized_rule = models.TextField(blank=True, null=True)
    ai_explanation = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['session', 'relationship_type', 'rule_a', 'rule_b']
    
    def __str__(self):
        return f"{self.rule_a} {self.relationship_type} {self.rule_b} ({self.confidence:.2f})"

class AISuggestion(models.Model):
    
    ACTION_CHOICES = [
        ('MERGE', 'Merge rules'),
        ('REMOVE_RULE_A', 'Remove Rule A'),
        ('REMOVE_RULE_B', 'Remove Rule B'), 
        ('KEEP_BOTH', 'Keep both rules'),
        ('REVIEW', 'Manual review needed'),
        ('REORDER', 'Reorder rules'),
    ]
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='ai_suggestions')
    relationship = models.ForeignKey(RuleRelationship, on_delete=models.CASCADE, null=True, blank=True)
    rule_a = models.CharField(max_length=50)
    rule_b = models.CharField(max_length=50)
    relationship_type = models.CharField(max_length=3, choices=RuleRelationship.RELATIONSHIP_TYPES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    optimized_rule = models.TextField()
    explanation = models.TextField()
    security_impact = models.TextField()
    performance_improvement = models.CharField(max_length=100)
    implementation_steps = models.JSONField()
    confidence_score = models.FloatField(default=0.0)
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_suggestions'
    
    def __str__(self):
        return f"AI: {self.rule_a} & {self.rule_b} -> {self.action}"

class AIOptimizationStrategy(models.Model):
    
    session = models.OneToOneField(RuleAnalysisSession, on_delete=models.CASCADE, related_name='ai_strategy')
    priority_actions = models.JSONField()
    rule_merging_plan = models.JSONField()
    removal_candidates = models.JSONField()
    performance_improvements = models.JSONField()
    security_considerations = models.JSONField()
    implementation_priority = models.JSONField()
    total_optimizations_suggested = models.IntegerField(default=0)
    estimated_performance_gain = models.FloatField(default=0.0)
    estimated_security_impact = models.CharField(max_length=20, default='NEUTRAL')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_optimization_strategies'
    
    def __str__(self):
        return f"AI Strategy for {self.session.name}"

"""

# FR03: Rule Performance Profiling Models
class RulePerformance(models.Model):
    rule_id = models.CharField(max_length=50, unique=True)
    hit_count = models.IntegerField(default=0)
    total_requests_processed = models.IntegerField(default=0)
    match_frequency = models.FloatField(default=0.0)
    average_evaluation_time = models.FloatField(default=0.0)
    effectiveness_ratio = models.FloatField(default=0.0)
    last_triggered = models.DateTimeField(null=True, blank=True)
    is_rarely_used = models.BooleanField(default=False)
    is_redundant = models.BooleanField(default=False)
    is_high_performance = models.BooleanField(default=False)
    ai_optimization_suggested = models.BooleanField(default=False)
    ai_optimization_type = models.CharField(max_length=50, blank=True, null=True)
    last_ai_analysis = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rule_performance'
    
    def __str__(self):
        return f"Performance: {self.rule_id} ({self.hit_count} hits)"

class PerformanceSnapshot(models.Model):
    snapshot_name = models.CharField(max_length=255)
    total_rules = models.IntegerField(default=0)
    rarely_used_count = models.IntegerField(default=0)
    redundant_count = models.IntegerField(default=0)
    high_performance_count = models.IntegerField(default=0)
    snapshot_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    ai_optimization_opportunities = models.IntegerField(default=0)
    estimated_ai_improvement = models.FloatField(default=0.0)
    
    class Meta:
        db_table = 'performance_snapshots'
    
    def __str__(self):
        return f"Snapshot: {self.snapshot_name}"

class RuleRankingSession(models.Model):
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('applied', 'Applied'),
    ]
    
    name = models.CharField(max_length=255)
    original_rules_order = models.JSONField()
    optimized_rules_order = models.JSONField()
    performance_improvement = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    approved_by = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    ai_generated = models.BooleanField(default=False)
    ai_confidence = models.FloatField(default=0.0)
    ai_optimization_rationale = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'rule_ranking_sessions'
    
    def __str__(self):
        return f"Ranking: {self.name} ({self.status})"

"""
# NEW: Model to track AI usage and performance
class AIUsageLog(models.Model):
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    response_time = models.FloatField(default=0.0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    cost_estimate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
    
    def __str__(self):
        return f"AI Usage: {self.endpoint} ({self.total_tokens} tokens)"

# FR04 Models - False Positive Detection
class FalsePositiveDetection(models.Model):
    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('analyzing', 'Analyzing'),
        ('resolved', 'Resolved'),
        ('whitelisted', 'Whitelisted')
    ]
    
    rule_id = models.CharField(max_length=50)
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='false_positives')
    false_positive_count = models.IntegerField(default=0)
    legitimate_request_count = models.IntegerField(default=0)
    false_positive_rate = models.FloatField(default=0.0)
    detection_method = models.CharField(max_length=20, default='manual')
    confidence_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    blocked_requests = models.JSONField(default=list)
    request_patterns = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'false_positive_detections'
        unique_together = ['rule_id', 'session']
    
    def __str__(self):
        return f"FP: {self.rule_id} ({self.false_positive_rate:.1%})"

class WhitelistSuggestion(models.Model):
    SUGGESTION_TYPES = [
        ('ip_whitelist', 'IP Whitelist'),
        ('path_whitelist', 'Path Whitelist'),
        ('user_agent_whitelist', 'User Agent Whitelist'),
        ('parameter_whitelist', 'Parameter Whitelist')
    ]
    
    STATUS_CHOICES = [
        ('suggested', 'Suggested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented')
    ]
    
    false_positive = models.ForeignKey(FalsePositiveDetection, on_delete=models.CASCADE, related_name='suggestions')
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    pattern_description = models.TextField()
    pattern_regex = models.TextField(blank=True, null=True)
    pattern_conditions = models.JSONField(default=dict)
    estimated_false_positive_reduction = models.FloatField(default=0.0)
    security_risk_assessment = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    implementation_priority = models.CharField(max_length=10, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='suggested')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'whitelist_suggestions'
    
    def __str__(self):
        return f"Whitelist: {self.suggestion_type} for {self.false_positive.rule_id}"

class LearningModeSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    name = models.CharField(max_length=255)
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='learning_sessions')
    learning_duration_hours = models.IntegerField(default=24)
    traffic_sample_size = models.IntegerField(default=1000)
    normal_traffic_patterns = models.JSONField(default=dict)
    baseline_metrics = models.JSONField(default=dict)
    anomaly_thresholds = models.JSONField(default=dict)
    patterns_learned = models.IntegerField(default=0)
    accuracy_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'learning_mode_sessions'
    
    def __str__(self):
        return f"Learning: {self.name} ({self.status})"

class WhitelistExport(models.Model):
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.CASCADE, related_name='exports')
    export_name = models.CharField(max_length=255)
    include_patterns = models.JSONField(default=list)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    total_patterns = models.IntegerField(default=0)
    file_size_bytes = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'whitelist_exports'
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"AI Usage {status}: {self.endpoint} ({self.total_tokens} tokens)"

"""