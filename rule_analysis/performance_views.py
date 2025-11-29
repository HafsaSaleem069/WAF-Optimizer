from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import pandas as pd
from .models import RulePerformance, PerformanceSnapshot
from .performance_analyzer import RulePerformanceProfiler
from supabase_client import supabase
from .supabase_utils import get_file_as_dataframe

@api_view(['POST'])
def analyze_rule_performance(request):
    """
    FR03: Analyze rule performance from traffic data - FIXED
    """
    try:
        traffic_file_id = request.data.get('traffic_file_id')
        rules_file_id = request.data.get('rules_file_id')
        snapshot_name = request.data.get('snapshot_name', 'Performance Analysis')
        
        print(f"🎯 Performance analysis request: traffic={traffic_file_id}, rules={rules_file_id}")
        
        # Validate required files
        if not traffic_file_id:
            return Response({'error': 'traffic_file_id is required'}, status=400)
        if not rules_file_id:
            return Response({'error': 'rules_file_id is required'}, status=400)
        
        # Get traffic file from Supabase
        try:
            resp = supabase.table('uploaded_files').select('*').eq('id', traffic_file_id).execute()
            recs = getattr(resp, 'data', None) or (resp.json().get('data') if hasattr(resp, 'json') else None)
            if not recs:
                return Response({'error': f'Traffic file with ID {traffic_file_id} not found'}, status=404)
            traffic_file = recs[0]
            traffic_data = get_file_as_dataframe(traffic_file)
            print(f"📊 Loaded traffic file: {traffic_file.get('filename')}, shape: {traffic_data.shape}")
        except Exception as e:
            return Response({'error': f'Error reading traffic file: {str(e)}'}, status=400)
        
        # Get rules file from Supabase
        try:
            resp = supabase.table('uploaded_files').select('*').eq('id', rules_file_id).execute()
            recs = getattr(resp, 'data', None) or (resp.json().get('data') if hasattr(resp, 'json') else None)
            if not recs:
                return Response({'error': f'Rules file with ID {rules_file_id} not found'}, status=404)
            rules_file = recs[0]
            rules_data = get_file_as_dataframe(rules_file)
            print(f"📋 Loaded rules file: {rules_file.get('filename')}, shape: {rules_data.shape}")
        except Exception as e:
            return Response({'error': f'Error reading rules file: {str(e)}'}, status=400)
        
        # Validate required columns in traffic data
        required_traffic_columns = ['rule_id']
        missing_columns = [col for col in required_traffic_columns if col not in traffic_data.columns]
        if missing_columns:
            return Response({
                'error': f'Traffic file missing required columns: {missing_columns}. Available columns: {list(traffic_data.columns)}'
            }, status=400)
        
        # Validate required columns in rules data
        if 'rule_id' not in rules_data.columns and 'id' not in rules_data.columns:
            return Response({
                'error': f'Rules file missing rule_id column. Available columns: {list(rules_data.columns)}'
            }, status=400)
        
        # Use 'id' column if 'rule_id' doesn't exist
        if 'rule_id' not in rules_data.columns and 'id' in rules_data.columns:
            rules_data['rule_id'] = rules_data['id']
        
        # Analyze performance with REAL data
        profiler = RulePerformanceProfiler()
        performance_data = profiler.analyze_traffic_data(rules_data, traffic_data)
        
        # Save to database
        results = profiler.save_performance_data(performance_data, snapshot_name)
        
        return Response({
            'status': 'success',
            'message': 'Rule performance analysis completed successfully!',
            'snapshot_id': results['snapshot_id'],
            'analysis_summary': {
                'total_rules_analyzed': results['total_rules_analyzed'],
                'rarely_used_rules': results['rarely_used_rules'],
                'redundant_rules': results['redundant_rules'],
                'high_performance_rules': results['high_performance_rules']
            },
            'performance_data': performance_data
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"🚨 Performance analysis error: {str(e)}")
        print(f"🔧 Traceback: {error_details}")
        return Response({
            'error': f'Performance analysis failed: {str(e)}'
        }, status=400)

@api_view(['GET'])
def get_performance_snapshot(request, snapshot_id):
    """
    Get performance analysis results
    """
    try:
        snapshot = PerformanceSnapshot.objects.get(id=snapshot_id)
        
        # Get detailed rule performance data for this snapshot
        rule_performance = RulePerformance.objects.filter(snapshot=snapshot).values()
        
        return Response({
            'snapshot_name': snapshot.snapshot_name,
            'summary_metrics': {
                'total_rules': snapshot.total_rules,
                'rarely_used_rules': snapshot.rarely_used_count,
                'redundant_rules': snapshot.redundant_count,
                'high_performance_rules': snapshot.high_performance_count,
                'average_hit_count': snapshot.average_hit_count
            },
            'rule_performance': list(rule_performance),
            'created_at': snapshot.created_at
        })
        
    except PerformanceSnapshot.DoesNotExist:
        return Response({'error': 'Performance snapshot not found'}, status=404)

@api_view(['GET'])
def get_rule_performance_dashboard(request):
    """
    Get overall performance dashboard data
    """
    try:
        # Get all performance data
        rules = RulePerformance.objects.all()
        
        # Calculate overall metrics
        total_rules = rules.count()
        rarely_used = rules.filter(is_rarely_used=True).count()
        redundant = rules.filter(is_redundant=True).count()
        high_perf = rules.filter(is_high_performance=True).count()
        
        # Performance statistics
        if total_rules > 0:
            avg_hit_count = sum(r.hit_count for r in rules) / total_rules
            avg_effectiveness = sum(r.effectiveness_ratio for r in rules) / total_rules
        else:
            avg_hit_count = 0
            avg_effectiveness = 0
        
        return Response({
            'overview_metrics': {
                'total_rules_monitored': total_rules,
                'rarely_used_rules': rarely_used,
                'redundant_rules': redundant,
                'high_performance_rules': high_perf,
                'average_hit_count': round(avg_hit_count, 2),
                'average_effectiveness': f"{avg_effectiveness:.1%}"
            },
            'performance_breakdown': {
                'efficiency_score': calculate_efficiency_score(rules),
                'optimization_opportunities': rarely_used + redundant,
                'top_performers': get_top_performers(rules)
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

# FIXED: Remove self parameter from helper functions
def calculate_efficiency_score(rules):
    """Calculate overall WAF efficiency score"""
    if not rules:
        return 0
    
    total_score = 0
    for rule in rules:
        # Score based on hit count and effectiveness
        hit_score = min(rule.hit_count / 100, 1.0) if rule.hit_count else 0
        effectiveness_score = rule.effectiveness_ratio if rule.effectiveness_ratio else 0
        total_score += (hit_score * 0.6 + effectiveness_score * 0.4)
    
    return round((total_score / len(rules)) * 100, 1)

def get_top_performers(rules, limit=5):
    """Get top performing rules"""
    scored_rules = []
    for rule in rules:
        hit_count = rule.hit_count if rule.hit_count else 0
        effectiveness = rule.effectiveness_ratio if rule.effectiveness_ratio else 0
        score = (hit_count * 0.6 + effectiveness * 100 * 0.4)
        scored_rules.append({
            'rule_id': rule.rule_id,
            'hit_count': hit_count,
            'effectiveness': f"{effectiveness:.1%}" if effectiveness else "0%",
            'performance_score': round(score, 1)
        })
    
    return sorted(scored_rules, key=lambda x: x['performance_score'], reverse=True)[:limit]
