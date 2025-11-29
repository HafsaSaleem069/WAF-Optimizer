import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.db import transaction
from .models import RulePerformance, PerformanceSnapshot

class RulePerformanceProfiler:
    """
    FR03: Rule Performance Profiling Engine
    Analyzes rule efficiency and identifies optimization opportunities
    """
    
    def __init__(self):
        self.analysis_results = {}
    
    def analyze_traffic_data(self, rules_df: pd.DataFrame, traffic_df: pd.DataFrame) -> dict:
        """
        FR03-01: Calculate hit counts and performance metrics from traffic data
        """
        performance_data = {}
        
        # Get unique rules from traffic data
        triggered_rules = traffic_df[traffic_df['rule_id'] != '-']['rule_id'].unique()
        
        for rule_id in triggered_rules:
            rule_traffic = traffic_df[traffic_df['rule_id'] == rule_id]
            
            # FR03-01: Hit counting
            hit_count = len(rule_traffic)
            total_requests = len(traffic_df)
            
            # FR03-02: Performance metrics
            match_frequency = hit_count / total_requests if total_requests > 0 else 0
            
            # Estimate evaluation time (use correct field name)
            average_evaluation_time = self.estimate_evaluation_time(rule_id, rule_traffic)
            
            # Effectiveness ratio (true positives / total hits)
            effectiveness = self.calculate_effectiveness(rule_traffic)
            
            performance_data[rule_id] = {
                'hit_count': hit_count,
                'total_requests_processed': total_requests,
                'match_frequency': match_frequency,
                'average_evaluation_time': average_evaluation_time,  # CORRECT FIELD NAME
                'effectiveness_ratio': effectiveness,
                'last_triggered': rule_traffic['timestamp'].max() if not rule_traffic.empty else None
            }
        
        # FR03-03: Flag inefficient rules
        self.flag_inefficient_rules(performance_data)
        
        return performance_data
    
    def estimate_evaluation_time(self, rule_id: str, rule_traffic: pd.DataFrame) -> float:
        """
        FR03-02: Estimate rule evaluation time based on complexity
        In real implementation, this would use actual timing data
        """
        # Simple heuristic based on rule characteristics
        base_time = 0.1  # milliseconds
        
        # More complex rules take longer
        complexity_factors = {
            'regex_patterns': 0.3,
            'multiple_conditions': 0.2,
            'data_transformations': 0.4
        }
        
        # Simplified estimation
        estimated_time = base_time
        
        # Add complexity factors (you would extract these from actual rule data)
        if any(keyword in rule_id.lower() for keyword in ['sql', 'xss', 'rce']):
            estimated_time += complexity_factors['regex_patterns']
        
        return estimated_time
    
    def calculate_effectiveness(self, rule_traffic: pd.DataFrame) -> float:
        """
        FR03-02: Calculate rule effectiveness (true positive rate)
        """
        if rule_traffic.empty:
            return 0.0
        
        # Count legitimate blocks vs false positives
        # This is simplified - real implementation would use threat intelligence
        total_hits = len(rule_traffic)
        false_positives = len(rule_traffic[rule_traffic.get('false_positive', False)])
        
        true_positives = total_hits - false_positives
        effectiveness = true_positives / total_hits if total_hits > 0 else 0.0
        
        return effectiveness
    
    def flag_inefficient_rules(self, performance_data: dict):
        """
        FR03-03: Identify rarely used and redundant rules
        """
        if not performance_data:
            return
        
        hit_counts = [data['hit_count'] for data in performance_data.values()]
        avg_hits = np.mean(hit_counts) if hit_counts else 0
        std_hits = np.std(hit_counts) if len(hit_counts) > 1 else 0
        
        for rule_id, data in performance_data.items():
            # FR03-03: Flag rarely used rules (significantly below average)
            is_rarely_used = data['hit_count'] < (avg_hits * 0.1)  # Less than 10% of average
            
            # FR03-03: Flag high performance rules (significantly above average)
            is_high_performance = data['hit_count'] > (avg_hits * 2)  # More than 200% of average
            
            # Flag potentially redundant rules (low effectiveness but high hits)
            is_redundant = (data['effectiveness_ratio'] < 0.3 and data['hit_count'] > avg_hits)
            
            data.update({
                'is_rarely_used': is_rarely_used,
                'is_high_performance': is_high_performance,
                'is_redundant': is_redundant
            })
    
    @transaction.atomic
    def save_performance_data(self, performance_data: dict, snapshot_name: str = "Performance Analysis"):
        """
        Save performance analysis to database
        """
        saved_rules = []
        
        for rule_id, data in performance_data.items():
            rule_perf, created = RulePerformance.objects.update_or_create(
                rule_id=rule_id,
                defaults={
                    'hit_count': data['hit_count'],
                    'total_requests_processed': data['total_requests_processed'],
                    'match_frequency': data['match_frequency'],
                    'average_evaluation_time': data['average_evaluation_time'],  # CORRECT FIELD NAME
                    'effectiveness_ratio': data['effectiveness_ratio'],
                    'last_triggered': data['last_triggered'],
                    'is_rarely_used': data['is_rarely_used'],
                    'is_redundant': data['is_redundant'],
                    'is_high_performance': data['is_high_performance']
                }
            )
            saved_rules.append(rule_perf)
        
        # Create performance snapshot
        rarely_used_count = len([r for r in saved_rules if r.is_rarely_used])
        redundant_count = len([r for r in saved_rules if r.is_redundant])
        high_perf_count = len([r for r in saved_rules if r.is_high_performance])
        
        snapshot = PerformanceSnapshot.objects.create(
            snapshot_name=snapshot_name,
            total_rules=len(saved_rules),
            rarely_used_count=rarely_used_count,
            redundant_count=redundant_count,
            high_performance_count=high_perf_count,
            average_hit_count=np.mean([r.hit_count for r in saved_rules]) if saved_rules else 0,
            snapshot_data=performance_data
        )
        
        return {
            'snapshot_id': snapshot.id,
            'total_rules_analyzed': len(saved_rules),
            'rarely_used_rules': rarely_used_count,
            'redundant_rules': redundant_count,
            'high_performance_rules': high_perf_count
        }