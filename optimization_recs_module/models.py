from django.db import models
from data_management.models import UploadedFile

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
    analysis_types = models.JSONField()  # List of analysis types to perform
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW: Store complete analysis results including AI suggestions
    results = models.JSONField(null=True, blank=True, help_text="Complete analysis results with AI suggestions")
    
    # NEW: AI-specific fields
    ai_available = models.BooleanField(default=False, help_text="Whether AI suggestions were available")
    ai_processed = models.BooleanField(default=False, help_text="Whether AI processing was attempted")
    ai_error = models.TextField(blank=True, null=True, help_text="Any AI processing errors")
    
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
    rule_a = models.CharField(max_length=50)  # Rule ID from rules file
    rule_b = models.CharField(max_length=50)  # Rule ID from rules file
    confidence = models.FloatField()  # 0.0 to 1.0
    evidence_count = models.IntegerField(default=0)
    conflicting_fields = models.JSONField()  # Fields causing the issue
    description = models.TextField()
    
    # NEW: AI suggestion fields
    ai_suggestion = models.JSONField(null=True, blank=True, help_text="AI optimization suggestion")
    ai_action = models.CharField(max_length=50, blank=True, null=True, help_text="AI recommended action")
    ai_optimized_rule = models.TextField(blank=True, null=True, help_text="AI suggested optimized rule")
    ai_explanation = models.TextField(blank=True, null=True, help_text="AI explanation for the suggestion")
    
    class Meta:
        unique_together = ['session', 'relationship_type', 'rule_a', 'rule_b']
    
    def __str__(self):
        return f"{self.rule_a} {self.relationship_type} {self.rule_b} ({self.confidence:.2f})"

# NEW: Model to store AI suggestions separately for better organization
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
    
    # Rule information
    rule_a = models.CharField(max_length=50)
    rule_b = models.CharField(max_length=50)
    relationship_type = models.CharField(max_length=3, choices=RuleRelationship.RELATIONSHIP_TYPES)
    
    # AI suggestion details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    optimized_rule = models.TextField(help_text="AI-generated optimized rule code")
    explanation = models.TextField(help_text="AI explanation for the suggestion")
    security_impact = models.TextField(help_text="Impact on security")
    performance_improvement = models.CharField(max_length=100, help_text="Expected performance gain")
    implementation_steps = models.JSONField(help_text="Step-by-step implementation guide")
    
    # Confidence and metadata
    confidence_score = models.FloatField(default=0.0)
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_suggestions'
        indexes = [
            models.Index(fields=['session', 'relationship_type']),
            models.Index(fields=['action']),
            models.Index(fields=['is_applied']),
        ]
    
    def __str__(self):
        return f"AI: {self.rule_a} & {self.rule_b} -> {self.action}"

# NEW: Model for overall AI optimization strategy
class AIOptimizationStrategy(models.Model):
    
    session = models.OneToOneField(RuleAnalysisSession, on_delete=models.CASCADE, related_name='ai_strategy')
    
    # Strategy components
    priority_actions = models.JSONField(help_text="High-priority actions sorted by impact")
    rule_merging_plan = models.JSONField(help_text="Specific rules to merge and approach")
    removal_candidates = models.JSONField(help_text="Rules that can be safely removed")
    performance_improvements = models.JSONField(help_text="Expected performance gains")
    security_considerations = models.JSONField(help_text="Security risks to watch for")
    implementation_priority = models.JSONField(help_text="Priority levels for each action")
    
    # Metadata
    total_optimizations_suggested = models.IntegerField(default=0)
    estimated_performance_gain = models.FloatField(default=0.0)
    estimated_security_impact = models.CharField(max_length=20, default='NEUTRAL', 
                                               choices=[('IMPROVED', 'Improved'), 
                                                       ('NEUTRAL', 'Neutral'), 
                                                       ('REDUCED', 'Reduced')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_optimization_strategies'
        verbose_name_plural = "AI Optimization Strategies"
    
    def __str__(self):
        return f"AI Strategy for {self.session.name}"

# NEW: Model to track AI usage and performance
class AIUsageLog(models.Model):
    
    session = models.ForeignKey(RuleAnalysisSession, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    response_time = models.FloatField(default=0.0)  # in seconds
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    cost_estimate = models.FloatField(default=0.0)  # estimated cost in USD
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_usage_logs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"AI Usage {status}: {self.endpoint} ({self.total_tokens} tokens)"
