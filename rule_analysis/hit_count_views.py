from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
from .hit_counter import RuleHitCounter
from .models import RulePerformance
from supabase_client import supabase
from .supabase_utils import get_file_as_dataframe

@api_view(['POST'])
def update_rule_hit_counts(request):
    """
    FR03-01, FR03-02 & FR03-03: Complete performance profiling - FIXED
    """
    try:
        # Get parameters from request
        traffic_file_id = request.data.get('traffic_file_id')
        rules_file_id = request.data.get('rules_file_id')
        # Raw content payloads (preferred from frontend)
        traffic_content = request.data.get('traffic_content') or request.data.get('logs_content') or request.data.get('traffic_file_content')
        rules_content = request.data.get('rules_content') or request.data.get('rules_file_content')
        update_type = request.data.get('update_type', 'incremental')
        
        print(f"🔄 Processing hit counts update: traffic={traffic_file_id}, rules={rules_file_id}")
        
        # Validate required parameters: if raw content provided, we don't need file ids
        if not traffic_file_id and not traffic_content:
            # Try to pick the most recent traffic file from Supabase metadata as a sensible default
            try:
                resp = supabase.table('uploaded_files').select('*').in_('file_type', ['traffic', 'logs']).order('uploaded_at', desc=True).limit(1).execute()
                recs = getattr(resp, 'data', None) or (resp.json().get('data') if hasattr(resp, 'json') else None)
                if recs and len(recs) > 0:
                    traffic_file_id = recs[0].get('id')
                else:
                    return Response({'error': 'traffic_file_id is required and no traffic files are available'}, status=400)
            except Exception:
                return Response({'error': 'traffic_file_id is required and could not query Supabase for defaults'}, status=400)
        
        # Load traffic data from Supabase — accept raw content or int ids or filename-like identifiers
        try:
            # If frontend sent raw content, prefer it
            raw_traffic_content = request.data.get('traffic_content') or request.data.get('logs_content') or request.data.get('traffic_file_content')
            if raw_traffic_content:
                import io
                if isinstance(raw_traffic_content, (bytes, bytearray)):
                    raw_traffic_content = raw_traffic_content.decode('utf-8')
                traffic_data = pd.read_csv(io.StringIO(raw_traffic_content))
            else:
                traffic_file = None

                def _extract_identifier(v):
                    if isinstance(v, dict):
                        return v.get('id') or v.get('filename') or v.get('name') or v.get('supabase_path') or v.get('key')
                    return v

                traffic_file_id_extracted = _extract_identifier(traffic_file_id)

                def _query_tables_eq(field, value):
                    for tbl in ('uploaded_files', 'files'):
                        try:
                            resp = supabase.table(tbl).select('*').eq(field, value).execute()
                            recs = getattr(resp, 'data', None) or (resp.json().get('data') if hasattr(resp, 'json') else None)
                            if recs:
                                recs[0]['_meta_table'] = tbl
                                return recs
                        except Exception:
                            continue
                    return None

                def _query_tables_or(expr):
                    for tbl in ('uploaded_files', 'files'):
                        try:
                            resp = supabase.table(tbl).select('*').or_(expr).execute()
                            recs = getattr(resp, 'data', None) or (resp.json().get('data') if hasattr(resp, 'json') else None)
                            if recs:
                                recs[0]['_meta_table'] = tbl
                                return recs
                        except Exception:
                            continue
                    return None

                def _query_tables_like(field, pattern):
                    for tbl in ('uploaded_files', 'files'):
                        try:
                            resp = supabase.table(tbl).select('*').like(field, pattern).execute()
                            recs = getattr(resp, 'data', None) or (resp.json().get('data') if hasattr(resp, 'json') else None)
                            if recs:
                                recs[0]['_meta_table'] = tbl
                                return recs
                        except Exception:
                            continue
                    return None

                # attempt numeric id
                try:
                    tid_int = int(traffic_file_id_extracted)
                except Exception:
                    tid_int = None

                if tid_int is not None:
                    recs = _query_tables_eq('id', tid_int)
                    if recs:
                        traffic_file = recs[0]
                if traffic_file is None and traffic_file_id_extracted:
                    recs = _query_tables_eq('filename', traffic_file_id_extracted)
                    if recs:
                        traffic_file = recs[0]
                if traffic_file is None and traffic_file_id_extracted:
                    recs = _query_tables_or(f"supabase_path.eq.{traffic_file_id_extracted},key.eq.{traffic_file_id_extracted}")
                    if recs:
                        traffic_file = recs[0]
                if traffic_file is None and traffic_file_id_extracted:
                    recs = _query_tables_like('filename', f"%{traffic_file_id_extracted}%")
                    if recs:
                        traffic_file = recs[0]

                if traffic_file is None:
                    return Response({'error': f'Traffic file with ID {traffic_file_id} not found'}, status=404)

                traffic_data = get_file_as_dataframe(traffic_file)
                print(f"📊 Loaded traffic file: {traffic_file.get('filename')}, shape: {traffic_data.shape}")

            # Validate required columns in traffic data
            if 'rule_id' not in traffic_data.columns:
                return Response({
                    'error': f'Traffic file missing required column: rule_id. Available columns: {list(traffic_data.columns)}'
                }, status=400)

        except Exception as e:
            return Response({'error': f'Error reading traffic file: {str(e)}'}, status=400)
        
        # Process the data
        hit_counter = RuleHitCounter()
        
        # FR03-01: Update hit counts
        hit_result = hit_counter.process_traffic_logs(traffic_data)
        
        # FR03-02: Calculate performance metrics
        total_requests = hit_result['total_requests_processed']
        metrics_result = hit_counter.calculate_performance_metrics(total_requests)
        
        # FR03-03: Flag inefficient rules
        flagged_rules = hit_counter.flag_inefficient_rules()
        
        return Response({
            'status': 'success',
            'message': 'Complete rule performance profiling completed',
            'summary': {
                'total_requests': total_requests,
                'rules_triggered': hit_result['rules_triggered'],
                'hits_updated': len(hit_result['hit_summary']),
                'metrics_calculated': len(metrics_result),
                'rules_flagged': {
                    'rarely_used': len(flagged_rules['rarely_used']),
                    'redundant': len(flagged_rules['redundant']),
                    'high_performance': len(flagged_rules['high_performance'])
                }
            },
            'hit_details': hit_result['hit_summary'],
            'performance_metrics': metrics_result,
            'flagged_rules': flagged_rules
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"🚨 Hit counts update error: {str(e)}")
        print(f"🔧 Traceback: {error_details}")
        return Response({'error': f'Update failed: {str(e)}'}, status=500)

@api_view(['GET'])
def get_hit_count_dashboard(request):
    """
    Get complete performance dashboard with FR03-01, FR03-02, FR03-03
    """
    try:
        hit_counter = RuleHitCounter()
        
        # Get basic stats
        hit_stats = hit_counter.get_rule_hit_stats()
        total_hits = sum(rule['hit_count'] for rule in hit_stats) if hit_stats else 0
        total_rules = len(hit_stats) if hit_stats else 0
        avg_hits_per_rule = total_hits / total_rules if total_rules > 0 else 0
        
        # Get performance metrics
        rules_with_metrics = RulePerformance.objects.all().values(
            'rule_id', 'hit_count', 'match_frequency', 'effectiveness_ratio',
            'is_rarely_used', 'is_redundant', 'is_high_performance'
        )
        
        # Enhanced top rules with metrics and flags
        top_rules = []
        for rule in rules_with_metrics.order_by('-hit_count')[:5]:
            flags = []
            if rule['is_rarely_used']:
                flags.append('Rarely Used')
            if rule['is_redundant']:
                flags.append('Redundant')
            if rule['is_high_performance']:
                flags.append('High Performer')
                
            top_rules.append({
                'rule_id': rule['rule_id'],
                'hit_count': rule['hit_count'],
                'match_frequency': f"{rule['match_frequency']:.2%}" if rule['match_frequency'] else "0%",
                'effectiveness_ratio': f"{rule['effectiveness_ratio']:.0%}" if rule['effectiveness_ratio'] else "0%",
                'flags': flags
            })
        
        # Get flagged rules summary
        flagged_summary = {
            'rarely_used': RulePerformance.objects.filter(is_rarely_used=True).count(),
            'redundant': RulePerformance.objects.filter(is_redundant=True).count(),
            'high_performance': RulePerformance.objects.filter(is_high_performance=True).count()
        }
        
        return Response({
            'summary': {
                'total_rules_tracked': total_rules,
                'total_hits_recorded': total_hits,
                'average_hits_per_rule': round(avg_hits_per_rule, 2),
                'flagged_rules_summary': flagged_summary
            },
            'top_performing_rules': top_rules,
            'all_rules': list(rules_with_metrics)
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def get_rule_hit_details(request, rule_id):
    """
    Get detailed hit information for a specific rule
    """
    try:
        hit_counter = RuleHitCounter()
        rule_stats = hit_counter.get_rule_hit_stats(rule_id)
        
        if not rule_stats:
            return Response({'error': f'Rule {rule_id} not found'}, status=404)
            
        # Get performance metrics for this specific rule
        try:
            rule_with_metrics = RulePerformance.objects.get(rule_id=rule_id)
            performance_data = {
                'match_frequency': f"{rule_with_metrics.match_frequency:.2%}" if rule_with_metrics.match_frequency else "0%",
                'effectiveness_ratio': f"{rule_with_metrics.effectiveness_ratio:.0%}" if rule_with_metrics.effectiveness_ratio else "0%",
                'average_evaluation_time': rule_with_metrics.average_evaluation_time,
                'flags': {
                    'is_rarely_used': rule_with_metrics.is_rarely_used,
                    'is_redundant': rule_with_metrics.is_redundant,
                    'is_high_performance': rule_with_metrics.is_high_performance
                }
            }
        except RulePerformance.DoesNotExist:
            performance_data = {}
            
        return Response({
            'rule_id': rule_stats['rule_id'],
            'hit_count': rule_stats['hit_count'],
            'last_triggered': rule_stats['last_triggered'],
            'performance_metrics': performance_data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)