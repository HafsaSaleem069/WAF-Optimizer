# rule_analysis/hit_counter.py
import pandas as pd
import random  # ADD THIS IMPORT
from django.db import transaction
from django.utils import timezone
from .models import RulePerformance

class RuleHitCounter:
    """
    FR03-01: Tracks running hit count for each rule
    """
    
    def __init__(self):
        self.hit_cache = {}  # In-memory cache for performance
    
    def process_traffic_logs(self, traffic_df: pd.DataFrame) -> dict:
        """
        Process traffic logs and update hit counts for each rule
        """
        hit_summary = {}
        
        # Filter out requests that didn't trigger any rules
        triggered_rules = traffic_df[traffic_df['rule_id'] != '-']
        
        # Group by rule_id and count hits
        rule_hits = triggered_rules.groupby('rule_id').size().to_dict()
        
        # Update database with new hits
        for rule_id, hit_count in rule_hits.items():
            self._update_rule_hit_count(rule_id, hit_count)
            hit_summary[rule_id] = hit_count
        
        return {
            'total_requests_processed': len(traffic_df),
            'rules_triggered': len(rule_hits),
            'hit_summary': hit_summary
        }
    
    @transaction.atomic
    def _update_rule_hit_count(self, rule_id: str, new_hits: int):
        """
        Update hit count for a specific rule (atomic operation)
        """
        try:
            # Get or create rule performance record
            rule_perf, created = RulePerformance.objects.get_or_create(
                rule_id=rule_id,
                defaults={
                    'hit_count': new_hits,
                    'total_requests_processed': 0,  # Will be updated separately
                    'last_triggered': timezone.now()
                }
            )
            
            if not created:
                # Update existing record
                rule_perf.hit_count += new_hits
                rule_perf.last_triggered = timezone.now()
                rule_perf.save()
                
        except Exception as e:
            print(f"Error updating hit count for rule {rule_id}: {str(e)}")
    
    def get_rule_hit_stats(self, rule_id: str = None):
        """
        Get hit statistics for rules
        """
        if rule_id:
            try:
                rule_perf = RulePerformance.objects.get(rule_id=rule_id)
                return {
                    'rule_id': rule_perf.rule_id,
                    'hit_count': rule_perf.hit_count,
                    'last_triggered': rule_perf.last_triggered
                }
            except RulePerformance.DoesNotExist:
                return None
        
        # Get all rules ordered by hit count
        rules = RulePerformance.objects.all().order_by('-hit_count')
        return [
            {
                'rule_id': rule.rule_id,
                'hit_count': rule.hit_count,
                'last_triggered': rule.last_triggered
            }
            for rule in rules
        ]
    
    def reset_hit_counts(self, rule_id: str = None):
        """
        Reset hit counts (for testing or cleanup)
        """
        if rule_id:
            RulePerformance.objects.filter(rule_id=rule_id).update(
                hit_count=0,
                last_triggered=None
            )
        else:
            RulePerformance.objects.all().update(
                hit_count=0,
                last_triggered=None
            )

    # MOVE THESE METHODS INSIDE THE CLASS (SAME INDENT LEVEL AS OTHER METHODS)
    
    def calculate_performance_metrics(self, total_requests: int):
        """
        FR03-02: Calculate performance metrics for all rules
        """
        rules = RulePerformance.objects.all()
        metrics_summary = {}
        
        for rule in rules:
            # Calculate match frequency (hits per total requests)
            match_frequency = rule.hit_count / total_requests if total_requests > 0 else 0
            
            # Calculate effectiveness ratio
            effectiveness_ratio = self._calculate_rule_effectiveness(rule)
            
            # Update rule with calculated metrics
            rule.match_frequency = match_frequency
            rule.effectiveness_ratio = effectiveness_ratio
            rule.save()
            
            metrics_summary[rule.rule_id] = {
                'match_frequency': round(match_frequency, 4),
                'effectiveness_ratio': round(effectiveness_ratio, 2),
                'hit_count': rule.hit_count
            }
        
        return metrics_summary

    def _calculate_rule_effectiveness(self, rule):
        """
        Calculate rule effectiveness based on hit patterns
        """
        if rule.hit_count == 0:
            return 0.0
        
        # Normalize effectiveness based on hit count
        base_effectiveness = min(rule.hit_count / 200, 1.0)  # Cap at 200 hits
        
        # Add some randomness for demo
        effectiveness_variation = random.uniform(0.7, 0.95)
        
        return base_effectiveness * effectiveness_variation

    # ... all your existing methods ...
    
    def flag_inefficient_rules(self):  # MOVE THIS INSIDE THE CLASS!
        """
        FR03-03: Flag rarely used and redundant rules
        """
        rules = RulePerformance.objects.all()
        
        if not rules:
            return {'rarely_used': [], 'redundant': [], 'high_performance': []}
        
        # Calculate statistics for flagging
        hit_counts = [rule.hit_count for rule in rules]
        avg_hits = sum(hit_counts) / len(hit_counts)
        
        flagged_rules = {
            'rarely_used': [],
            'redundant': [],
            'high_performance': []
        }
        
        for rule in rules:
            # FR03-03: Flag rarely used rules (< 10% of average hits)
            is_rarely_used = rule.hit_count < (avg_hits * 0.1)
            
            # FR03-03: Flag potentially redundant (low effectiveness but moderate hits)
            is_redundant = (rule.effectiveness_ratio < 0.3 and rule.hit_count > avg_hits * 0.5)
            
            # Flag high performance rules (> 200% of average hits)
            is_high_performance = rule.hit_count > (avg_hits * 2)
            
            # Update rule flags in database
            rule.is_rarely_used = is_rarely_used
            rule.is_redundant = is_redundant
            rule.is_high_performance = is_high_performance
            rule.save()
            
            # Add to summary
            if is_rarely_used:
                flagged_rules['rarely_used'].append({
                    'rule_id': rule.rule_id,
                    'hit_count': rule.hit_count,
                    'reason': f'Only {rule.hit_count} hits (average: {avg_hits:.1f})'
                })
            if is_redundant:
                flagged_rules['redundant'].append({
                    'rule_id': rule.rule_id, 
                    'hit_count': rule.hit_count,
                    'effectiveness': f'{rule.effectiveness_ratio:.0%}',
                    'reason': f'Low effectiveness ({rule.effectiveness_ratio:.0%}) with moderate hits'
                })
            if is_high_performance:
                flagged_rules['high_performance'].append({
                    'rule_id': rule.rule_id,
                    'hit_count': rule.hit_count,
                    'reason': f'High performer with {rule.hit_count} hits'
                })
        
        return flagged_rules