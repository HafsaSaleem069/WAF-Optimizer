from rest_framework import serializers
from .models import RuleAnalysisSession, RuleRelationship

class RuleRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleRelationship
        fields = '__all__'

class RuleAnalysisSessionSerializer(serializers.ModelSerializer):
    relationships = RuleRelationshipSerializer(many=True, read_only=True)
    
    class Meta:
        model = RuleAnalysisSession
        fields = '__all__'