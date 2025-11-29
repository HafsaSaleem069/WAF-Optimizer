from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
import pandas as pd
import json
#from .models import RuleAnalysisSession, RuleRelationship
from data_management.models import UploadedFile
import io
from rest_framework import status
from django.shortcuts import get_object_or_404
from .supabase_utils import get_file_as_string, get_file_as_dataframe

"""
class RuleAnalysisSessionViewSet(viewsets.ModelViewSet):
    
    queryset = RuleAnalysisSession.objects.all()
    
    def get_serializer_class(self):
        from .serializers import RuleAnalysisSessionSerializer
        return RuleAnalysisSessionSerializer
"""
def _flatten_relationships(relationships_dict):
    """Convert relationships dictionary to flat list for API response"""
    flattened = []
    for rel_type, rel_list in relationships_dict.items():
        flattened.extend(rel_list)
    return flattened

@api_view(['POST'])
def analyze_rules(request):
    """Enhanced rule analysis endpoint with AI integration - accepts file content"""
    try:
        print("Analyze rules endpoint called!")
        
        # Support session-based analysis: load files for provided session_id
        if request.data.get('session_id'):
            session_id = request.data.get('session_id')
            session = get_object_or_404(RuleAnalysisSession, id=session_id)
            if session.rules_file and session.traffic_file:
                try:
                    rules_content = get_file_as_string(session.rules_file)
                    logs_content = get_file_as_string(session.traffic_file)
                    analysis_types = request.data.get('analysis_types', session.analysis_types or ['SHD', 'RXD'])
                except Exception as e:
                    # Distinguish network/storage problems and return 502 to the frontend
                    err_msg = str(e)
                    print(f"Error loading session files for session {session_id}: {err_msg}")
                    return Response({'error': f'Failed to load session files: {err_msg}'}, status=status.HTTP_502_BAD_GATEWAY)
            else:
                return Response({'error': 'Session does not reference both rules and traffic files'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if files are sent as multipart/form-data
        elif request.FILES:
            print("Processing files from multipart/form-data...")
            rules_file = request.FILES.get('rules_file')
            logs_file = request.FILES.get('logs_file')  
            analysis_types = request.data.get('analysis_types', ['SHD', 'RXD'])
            
            print(f"Received files: rules_file={rules_file.name if rules_file else None}, logs_file={logs_file.name if logs_file else None}")
            
            if not rules_file or not logs_file:
                return Response(
                    {'error': 'Both rules_file and logs_file are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Read file content
            rules_content = rules_file.read().decode('utf-8')
            logs_content = logs_file.read().decode('utf-8')
            
        # Check if files are sent as JSON with content strings
        elif request.data.get('rules_content') and request.data.get('logs_content'):
            print("Processing files from JSON content...")
            rules_content = request.data.get('rules_content')
            logs_content = request.data.get('logs_content')
            analysis_types = request.data.get('analysis_types', ['SHD', 'RXD'])
            
        else:
            return Response(
                {'error': 'Either send files as multipart/form-data or provide rules_content and logs_content in JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # DEBUG: Print file info
        print(f"=== DEBUG FILE INFO ===")
        print(f"Rules content length: {len(rules_content)}")
        print(f"Logs content length: {len(logs_content)}")
        print(f"Analysis types: {analysis_types}")
        print(f"=======================")
        
        # Create DataFrames from content
        try:
            print("Creating DataFrames from content...")
            rules_df = pd.read_csv(io.StringIO(rules_content))
            logs_df = pd.read_csv(io.StringIO(logs_content))
            
            print(f"Rules data shape: {rules_df.shape}")
            print(f"Logs data shape: {logs_df.shape}")
            
        except Exception as e:
            print(f"Error creating DataFrames: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Error parsing CSV data: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )               
        
        # Perform analysis with AI
        try:
            print("Starting rule analysis with AI...")
            
            # Initialize analyzer with AI enabled
            analyzer = RuleRelationshipAnalyzer(
                rules_df=rules_df,
                traffic_df=logs_df,  # Using logs_df as traffic data
                enable_ai=True  # Enable AI suggestions
            )
            
            # Perform analysis (this now includes AI suggestions)
            analysis_results = analyzer.analyze_all_relationships(analysis_types)
            
            print(f"Analysis completed. Total relationships found: {analysis_results.get('total_relationships', 0)}")
            
            # Create or reuse analysis session record
            if request.data.get('session_id'):
                session = get_object_or_404(RuleAnalysisSession, id=request.data.get('session_id'))
            else:
                session = RuleAnalysisSession.objects.create(
                    name=f"Analysis Session {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                    analysis_types=analysis_types
                )
            
            # Store individual relationships
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
            
            # Prepare response data in the format expected by frontend
            response_data = {
                'total_rules': analysis_results.get('total_rules', 0),
                'total_relationships': analysis_results.get('total_relationships', 0),
                'relationships': analysis_results.get('relationships', {}),
                'shd_count': analysis_results.get('shd_count', 0),
                'rxd_count': analysis_results.get('rxd_count', 0),
                'sub_count': analysis_results.get('sub_count', 0),
                'cor_count': analysis_results.get('cor_count', 0),
                'recommendations': analysis_results.get('recommendations', []),
                'sample_rules': analysis_results.get('sample_rules', []),
                'ai_available': analysis_results.get('ai_available', False),
                'ai_suggestions': analysis_results.get('ai_suggestions', {})
            }
            
            # Add AI error if present
            if analysis_results.get('ai_error'):
                response_data['ai_error'] = analysis_results.get('ai_error')
            
            return Response({
                'data': response_data
            })
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        print(f"Error in analyze_rules: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
@api_view(['GET'])
def get_analysis_session(request, session_id):
    """Get specific analysis session"""
    try:
        session = get_object_or_404(RuleAnalysisSession, id=session_id)
        
        # Get relationships for this session
        relationships = session.relationships.all()
        
        # Prepare response data
        response_data = {
            'session_id': session.id,
            'created_at': session.created_at,
            'rules_file': session.rules_file.file.name if session.rules_file else None,
            'traffic_file': session.traffic_file.file.name if session.traffic_file else None,
            'analysis_types': session.analysis_types,
            'total_rules_analyzed': relationships.count() * 2,  # Approximate
            'relationships_found': relationships.count(),
            'relationships': [
                {
                    'rule_a': rel.rule_a,
                    'rule_b': rel.rule_b,
                    'relationship_type': rel.relationship_type,
                    'confidence': rel.confidence,
                    'description': rel.description,
                    'evidence_count': rel.evidence_count,
                    'conflicting_fields': rel.conflicting_fields
                }
                for rel in relationships
            ],
            'ai_available': False,  # For now, until we implement proper storage
            'analysis_summary': {
                'shd_count': relationships.filter(relationship_type='SHD').count(),
                'rxd_count': relationships.filter(relationship_type='RXD').count(),
                'total_rules': relationships.count() * 2
            }
        }
        
        return Response({
            'status': 'success',
            'data': response_data
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get session: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )