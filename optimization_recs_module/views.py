# analysis_app/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
import pandas as pd
import io
import json
import traceback
from .models import RuleAnalysisSession, RuleRelationship # Assuming these models exist
from .rule_analyzer import RuleRelationshipAnalyzer # Import the local analyzer file

# NOTE: Mocking external utility imports based on context
# from data_management.models import UploadedFile
# from .supabase_utils import get_file_as_string, get_file_as_dataframe

# --- Class-Based Views (for CRUD operations on sessions) ---

class RuleAnalysisSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for creating, listing, retrieving, and updating rule analysis sessions."""
    
    # You will need to define the serializer in a separate serializers.py file.
    # from .serializers import RuleAnalysisSessionSerializer 
    
    queryset = RuleAnalysisSession.objects.all()
    # def get_serializer_class(self): ... # (Omitted for brevity here)


# --- Function-Based Views (for API actions) ---

def _flatten_relationships(relationships_dict):
    """Convert relationships dictionary to flat list for API response"""
    flattened = []
    for rel_type, rel_list in relationships_dict.items():
        flattened.extend(rel_list)
    return flattened


@api_view(['POST'])
def analyze_rules(request):
    """
    Enhanced rule analysis endpoint with AI integration.
    Accepts CSV content via files, JSON, or a session ID.
    """
    try:
        # --- 1. DATA INGESTION ---
        rules_content, logs_content, analysis_types = None, None, ['SHD', 'RXD']
        session_id = request.data.get('session_id')

        # Logic for loading files from a Session (requires Supabase integration)
        if session_id:
            session = get_object_or_404(RuleAnalysisSession, id=session_id)
            # NOTE: Assuming get_file_as_string and session.rules_file/traffic_file work
            # rules_content = get_file_as_string(session.rules_file)
            # logs_content = get_file_as_string(session.traffic_file)
            # analysis_types = request.data.get('analysis_types', session.analysis_types or ['SHD', 'RXD'])
            return Response({'error': 'Session loading mocked/disabled for brevity'}, status=status.HTTP_501_NOT_IMPLEMENTED) # Placeholder

        # Logic for processing files sent via multipart/form-data
        elif request.FILES:
            rules_file = request.FILES.get('rules_file')
            logs_file = request.FILES.get('logs_file')
            
            if not rules_file or not logs_file:
                return Response({'error': 'Both rules_file and logs_file are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            rules_content = rules_file.read().decode('utf-8')
            logs_content = logs_file.read().decode('utf-8')
            analysis_types = request.data.get('analysis_types', ['SHD', 'RXD'])

        # Logic for processing content sent via JSON strings
        elif request.data.get('rules_content') and request.data.get('logs_content'):
            rules_content = request.data.get('rules_content')
            logs_content = request.data.get('logs_content')
            analysis_types = request.data.get('analysis_types', ['SHD', 'RXD'])
            
        else:
            return Response({'error': 'No file content provided'}, status=status.HTTP_400_BAD_REQUEST)

        # --- 2. DATA FRAME CREATION ---
        try:
            rules_df = pd.read_csv(io.StringIO(rules_content))
            logs_df = pd.read_csv(io.StringIO(logs_content))
        except Exception as e:
            return Response({'error': f'Error parsing CSV data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # --- 3. ANALYSIS AND AI INTEGRATION ---
        analyzer = RuleRelationshipAnalyzer(
            rules_df=rules_df,
            traffic_df=logs_df,
            enable_ai=True
        )
        
        analysis_results = analyzer.analyze_all_relationships(analysis_types)
        
        # --- 4. PERSISTENCE (Django ORM) ---
        
        # Create or reuse analysis session record
        if session_id:
            session = get_object_or_404(RuleAnalysisSession, id=session_id)
        else:
            session = RuleAnalysisSession.objects.create(
                name=f"Analysis Session {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                analysis_types=analysis_types
            )
        
        # Store individual relationships (AI suggestions are embedded in 'analysis_results')
        relationships = analysis_results.get('relationships', {})
        for rel_type, rel_list in relationships.items():
            for rel in rel_list:
                RuleRelationship.objects.create(
                    session=session,
                    rule_a=rel.get('rule_a'),
                    rule_b=rel.get('rule_b'),
                    relationship_type=rel.get('relationship_type'),
                    confidence=rel.get('confidence', 0),
                    description=rel.get('description', ''),
                    evidence_count=rel.get('evidence_count', 0),
                    conflicting_fields=rel.get('conflicting_fields', {})
                )
        
        # --- 5. RESPONSE ---
        response_data = analysis_results.copy() # Return the full analysis including AI suggestions
        
        return Response({'data': response_data}, status=status.HTTP_200_OK)
            
    except Exception as e:
        # Catch all for unexpected errors
        print(f"Error: {traceback.format_exc()}")
        return Response({'error': f'Analysis failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_analysis_session(request, session_id):
    """Get specific analysis session and its relationships."""
    try:
        session = get_object_or_404(RuleAnalysisSession, id=session_id)
        relationships = session.relationships.all()
        
        # Prepare response data (simplified/cleaned structure)
        response_data = {
            'session_id': session.id,
            'created_at': session.created_at,
            'analysis_types': session.analysis_types,
            'total_relationships': relationships.count(),
            'relationships': [
                {
                    'rule_a': rel.rule_a,
                    'rule_b': rel.rule_b,
                    'type': rel.relationship_type,
                    'confidence': rel.confidence,
                    'description': rel.description,
                    'evidence_count': rel.evidence_count,
                    'conflicting_fields': rel.conflicting_fields
                }
                for rel in relationships
            ],
            'summary': {
                'shd_count': relationships.filter(relationship_type='SHD').count(),
                'rxd_count': relationships.filter(relationship_type='RXD').count(),
            }
        }
        
        return Response({'status': 'success', 'data': response_data}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': f'Failed to get session: {str(e)}'}, status=status.HTTP_404_NOT_FOUND)