# false_positive/serializers.py

from rest_framework import serializers
from .models import FalsePositiveDetection, WhitelistSuggestion
from optimization_recs_module.models import RuleAnalysisSession

class FalsePositiveDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FalsePositiveDetection
        fields = [
            'id', 'session', 'rule_id', 'false_positive_count', 
            'legitimate_request_count', 'false_positive_rate', 
            'detection_method', 'confidence_score', 'blocked_requests', 
            'request_patterns', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WhitelistSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhitelistSuggestion
        fields = [
            'id', 'false_positive', 'suggestion_type', 
            'pattern_description', 'pattern_regex', 
            'pattern_conditions', 'estimated_false_positive_reduction', 
            'security_risk_assessment', 'implementation_priority', 
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RuleAnalysisSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleAnalysisSession
        fields = ['id', 'name', 'analysis_types', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
