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
import re
import uuid
import traceback
from .models import RuleAnalysisSession, RuleRelationship # Assuming these models exist
from .rule_analyzer import RuleRelationshipAnalyzer # Import the local analyzer file
from .file_storage_utils import save_file_content_by_name

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
    
@api_view(['POST'])
def api_apply_optimization(request):
    """
    Receives an optimization instruction (MERGE, REMOVE_A, REMOVE_B),
    the current rules content, and applies the change, returning the new CSV string.
    
    EXPECTED PAYLOAD (from frontend/utils.py):
    {
        "rules_file_name": "filename.csv", 
        "rules_content": "Rule_ID,Pattern,...", 
        "relationship_data": {...}, 
        "action": "REMOVE_RULE_B"
    }
    """
    try:
        print("API Apply Optimization called with data.")
        
        # 1. Data Retrieval (Using filename and content from frontend)
        rules_file_name = request.data.get('rules_file_name')
        rules_csv_content = request.data.get('rules_content')
        relationship_data = request.data.get('relationship_data')
        action = request.data.get('action')
        
        if not all([rules_file_name, rules_csv_content, relationship_data, action]):
            return Response({"status": "error", "message": "Missing required data (rules_file_name, rules_content, action, or relationship_data)"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Parse and Prepare DataFrame (No file lookup needed)
        rules_df = pd.read_csv(io.StringIO(rules_csv_content))
        modified_df = rules_df.copy()

        ai_suggestion = relationship_data.get('ai_suggestion', {})
        
        # NOTE: Rule IDs from the frontend are strings. Ensure comparison is safe.
        rule_a_id = str(relationship_data.get('rule_a'))
        rule_b_id = str(relationship_data.get('rule_b'))
        optimized_rule_syntax = ai_suggestion.get('optimized_rule', '')
        
        # Filter column name for safety
        ID_COL = 'rule_id'

        # 3. Apply Modification Logic
        
        if action == 'REMOVE_RULE_A':
            # Filter DataFrame where ID column value (converted to string) is not equal to rule_a_id
            modified_df = modified_df[modified_df[ID_COL].astype(str) != rule_a_id]
            message = f"Rule {rule_a_id} successfully removed."

        elif action == 'REMOVE_RULE_B':
            # Filter DataFrame where ID column value (converted to string) is not equal to rule_b_id
            modified_df = modified_df[modified_df[ID_COL].astype(str) != rule_b_id]
            message = f"Rule {rule_b_id} successfully removed."

        elif action == 'MERGE':
            if not optimized_rule_syntax or optimized_rule_syntax.strip() == '':
                return Response({"status": "error", "message": "MERGE action requires optimized rule syntax."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove old rules (A and B) - Filter out rows where ID matches rule_a_id or rule_b_id
            modified_df = modified_df[~modified_df[ID_COL].astype(str).isin([rule_a_id, rule_b_id])]
            
            # Use UUID if ID is not extractable (safer)
            id_match = re.search(r'id:(\d+)', optimized_rule_syntax)
            new_id = id_match.group(1) if id_match else f"MERGED-{str(uuid.uuid4())[:8]}" # Keep as string if UUID
            
            # Create the new merged rule row (using Rule A as the template for default values)
            rule_a_row = rules_df[rules_df[ID_COL].astype(str) == rule_a_id].iloc[0]
            new_rule_row = rule_a_row.copy()

            new_rule_row[ID_COL] = new_id
            new_rule_row['Pattern'] = optimized_rule_syntax
            new_rule_row['Description'] = f"MERGED: {rule_a_id} & {rule_b_id} (AI Optimized)"
            
            # Append new rule
            modified_df = pd.concat([modified_df, pd.DataFrame([new_rule_row])], ignore_index=True)
            message = f"Rules {rule_a_id} and {rule_b_id} merged into new rule {new_id}."
            
        else:
            return Response({"status": "error", "message": f"Unsupported action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Finalize and Save
        new_csv_content = modified_df.to_csv(index=False)
        # Use the name (unique key) for saving to Supabase
        save_successful = save_file_content_by_name(rules_file_name, new_csv_content)

        if not save_successful:
            # If Supabase saving failed, return a server error
            return Response({"status": "error", "message": "Failed to persist optimized file to storage."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 5. Response
        return Response({
            "status": "success", 
            "message": message,
            "new_csv_content": new_csv_content
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Catch all for unexpected errors
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")
        return Response({"status": "error", "message": f"Server error applying optimization: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)