# rule_analysis/ranking_algorithm.py
import pandas as pd
import numpy as np
from typing import List, Dict
from django.db import transaction
from .models import RulePerformance, RuleRankingSession

class SmartRuleRanker:
    """
    FR05-01: Implements the "Smart Order" feature with FR03 integration
    """

    def process_real_rules_data(self, rules_df: pd.DataFrame):
        """
        Process real rules CSV data into the format needed for ranking
        """
        processed_rules = []
        
        # Handle different possible CSV structures
        if 'rule_id' in rules_df.columns:
            # Standard format: rule_id, category, description, etc.
            for position, (_, rule) in enumerate(rules_df.iterrows(), 1):
                processed_rules.append({
                    'rule_id': str(rule['rule_id']),  # Ensure string type
                    'position': position,
                    'category': rule.get('category', 'Unknown'),
                    'description': rule.get('description', 'No description'),
                    'rule_data': rule.to_dict()
                })
        elif 'id' in rules_df.columns:
            # Alternative format with 'id' instead of 'rule_id'
            for position, (_, rule) in enumerate(rules_df.iterrows(), 1):
                processed_rules.append({
                    'rule_id': str(rule['id']),  # Use 'id' as rule_id
                    'position': position,
                    'category': rule.get('category', 'Unknown'),
                    'description': rule.get('description', 'No description'),
                    'rule_data': rule.to_dict()
                })
        else:
            # Fallback: use first column as rule_id
            first_col = rules_df.columns[0]
            for position, (_, rule) in enumerate(rules_df.iterrows(), 1):
                processed_rules.append({
                    'rule_id': str(rule[first_col]),
                    'position': position,
                    'category': rule.get('category', 'Unknown'),
                    'description': rule.get('description', 'No description'),
                    'rule_data': rule.to_dict()
                })
        
        return pd.DataFrame(processed_rules)

    def enhance_with_fr03_data(self, rules_data: pd.DataFrame, performance_data: pd.DataFrame) -> pd.DataFrame:
        """
        Step 3: Enhance ranking with comprehensive FR03 performance data
        Uses all FR03 metrics: hit_count, effectiveness_ratio, match_frequency, flags
        """
        enhanced_rules = []
        
        for _, rule in rules_data.iterrows():
            rule_id = rule['rule_id']
            
            # Get comprehensive FR03 performance data
            try:
                rule_perf = RulePerformance.objects.get(rule_id=rule_id)
                
                # Use ALL FR03 metrics for smarter ranking
                enhanced_rule = {
                    'rule_id': rule_id,
                    'rule_data': self.convert_to_python_types(rule.to_dict()),
                    'position': rule.get('position', 0),
                    
                    # FR03 Performance Metrics
                    'hit_count': rule_perf.hit_count,
                    'effectiveness_ratio': rule_perf.effectiveness_ratio,
                    'match_frequency': rule_perf.match_frequency,
                    'average_evaluation_time': rule_perf.average_evaluation_time,
                    
                    # FR03 Efficiency Flags
                    'is_rarely_used': rule_perf.is_rarely_used,
                    'is_redundant': rule_perf.is_redundant,
                    'is_high_performance': rule_perf.is_high_performance,
                    
                    # Additional context
                    'last_triggered': rule_perf.last_triggered,
                    'total_requests_processed': rule_perf.total_requests_processed
                }
                
            except RulePerformance.DoesNotExist:
                # If no FR03 data, use basic info with low priority
                enhanced_rule = {
                    'rule_id': rule_id,
                    'rule_data': self.convert_to_python_types(rule.to_dict()),
                    'position': rule.get('position', 0),
                    'hit_count': 0,
                    'effectiveness_ratio': 0.1,  # Low priority for unknown rules
                    'match_frequency': 0.0,
                    'average_evaluation_time': 0.0,
                    'is_rarely_used': True,  # Assume rarely used if no data
                    'is_redundant': False,
                    'is_high_performance': False,
                    'last_triggered': None,
                    'total_requests_processed': 0
                }
            
            enhanced_rules.append(enhanced_rule)
        
        return pd.DataFrame(enhanced_rules)

    def calculate_rule_priority_score(self, rule_data: Dict) -> float:
        """
        Step 3: Enhanced priority scoring using ALL FR03 metrics
        """
        # Weights for different factors
        weights = {
            'hit_count': 0.35,           # Frequency of triggering
            'effectiveness_ratio': 0.25,  # Success rate
            'match_frequency': 0.15,      # How often it matches
            'performance_flags': 0.15,    # FR03 efficiency flags
            'recency': 0.10              # Recent activity
        }
        
        # Normalize hit count (0 to 1 scale)
        max_hits = max(rule_data['hit_count'], 1)
        hit_score = rule_data['hit_count'] / max_hits
        
        # Effectiveness ratio (already 0-1)
        effectiveness_score = rule_data['effectiveness_ratio']
        
        # Match frequency (already 0-1)
        frequency_score = min(rule_data['match_frequency'] * 10, 1.0)  # Scale appropriately
        
        # Performance flags score
        flags_score = 0.0
        if rule_data['is_high_performance']:
            flags_score += 0.3
        if not rule_data['is_rarely_used']:
            flags_score += 0.4
        if not rule_data['is_redundant']:
            flags_score += 0.3
        
        # Recency bonus (rules triggered recently get boost)
        recency_score = 0.1 if rule_data['last_triggered'] else 0.0
        
        # Penalize rarely used and redundant rules more heavily
        penalties = 0.0
        if rule_data['is_rarely_used']:
            penalties += 0.3
        if rule_data['is_redundant']:
            penalties += 0.2
        
        # Calculate final score
        priority_score = (
            weights['hit_count'] * hit_score +
            weights['effectiveness_ratio'] * effectiveness_score +
            weights['match_frequency'] * frequency_score +
            weights['performance_flags'] * flags_score +
            weights['recency'] * recency_score -
            penalties
        )
        
        # Ensure score is between 0 and 1
        return max(0.0, min(priority_score, 1.0))

    def convert_to_python_types(self, data):
        """
        Convert pandas/numpy types to Python native types for JSON serialization
        """
        if isinstance(data, (np.integer, pd.Int64Dtype)):
            return int(data)
        elif isinstance(data, (np.floating, pd.Float64Dtype)):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, pd.Series):
            return data.tolist()
        elif isinstance(data, dict):
            return {key: self.convert_to_python_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.convert_to_python_types(item) for item in data]
        else:
            return data

    def generate_optimized_ranking(self, rules_data: pd.DataFrame, performance_data: pd.DataFrame) -> List[Dict]:
        """
        Step 3: Generate optimized ranking using enhanced FR03 data
        """
        # Enhance rules with comprehensive FR03 data
        enhanced_rules_df = self.enhance_with_fr03_data(rules_data, performance_data)
        
        optimized_rules = []
        
        for _, rule in enhanced_rules_df.iterrows():
            # Calculate priority score using ALL FR03 metrics
            priority_score = self.calculate_rule_priority_score(rule.to_dict())
            
            optimized_rules.append({
                'rule_id': rule['rule_id'],
                'rule_data': self.convert_to_python_types(rule['rule_data']),
                'priority_score': float(priority_score),
                'hit_count': int(rule['hit_count']),
                'effectiveness_ratio': float(rule['effectiveness_ratio']),
                'match_frequency': float(rule['match_frequency']),
                'is_high_performance': bool(rule['is_high_performance']),
                'is_rarely_used': bool(rule['is_rarely_used']),
                'is_redundant': bool(rule['is_redundant']),
                'current_position': int(rule['position'])
            })
        
        # Sort by priority score (highest first)
        optimized_rules.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Assign new positions
        for new_position, rule in enumerate(optimized_rules, 1):
            rule['new_position'] = int(new_position)
            rule['position_change'] = int(rule['current_position'] - new_position)
        
        return optimized_rules

    def calculate_performance_improvement(self, current_order: List, optimized_order: List) -> float:
        """
        FR05-04: Estimate performance improvement
        """
        total_rules = len(current_order)
        
        if total_rules == 0:
            return 0.0
        
        # Calculate average position in current order (lower = better)
        current_avg_position = sum(range(1, total_rules + 1)) / total_rules
        
        # Calculate weighted average position in optimized order
        optimized_weighted_sum = 0
        total_hits = 0
        
        for rule in optimized_order:
            position = rule['new_position']
            hit_count = rule['hit_count']
            optimized_weighted_sum += position * hit_count
            total_hits += hit_count
        
        optimized_avg_position = optimized_weighted_sum / total_hits if total_hits > 0 else current_avg_position
        
        # Improvement percentage (lower score = better)
        improvement = ((current_avg_position - optimized_avg_position) / current_avg_position) * 100
        
        return float(max(improvement, 0))

    @transaction.atomic
    def create_ranking_session(self, rules_df: pd.DataFrame, performance_data: pd.DataFrame, session_name: str) -> RuleRankingSession:
        """
        FR05-02: Create and save a ranking proposal using REAL data
        """
        # Process real rules data
        processed_rules_df = self.process_real_rules_data(rules_df)
        
        # Get current order from processed rules
        current_order = []
        for _, rule in processed_rules_df.iterrows():
            current_order.append({
                'rule_id': rule['rule_id'],
                'position': int(rule['position']),
                'rule_data': self.convert_to_python_types(rule.to_dict())
            })
        
        # Generate optimized order
        optimized_order = self.generate_optimized_ranking(processed_rules_df, performance_data)
        
        # Calculate improvement
        improvement = self.calculate_performance_improvement(current_order, optimized_order)
        
        # Create ranking session
        ranking_session = RuleRankingSession.objects.create(
            name=session_name,
            original_rules_order=self.convert_to_python_types(current_order),
            optimized_rules_order=self.convert_to_python_types(optimized_order),
            performance_improvement=float(improvement),
            status='proposed'
        )
        
        return ranking_session
    
    def calculate_performance_improvement(self, current_order: List, optimized_order: List) -> float:
        """
        FR05-04: More realistic performance improvement estimation
        """
        total_rules = len(current_order)
        
        if total_rules == 0:
            return 0.0
        
        # More realistic calculation based on weighted average processing
        total_processing_time = 0
        optimized_processing_time = 0
        
        for rule in optimized_order:
            current_pos = next(r['position'] for r in current_order if r['rule_id'] == rule['rule_id'])
            optimized_pos = rule['new_position']
            
            # Assume each rule check takes time proportional to its complexity
            rule_processing_weight = rule['hit_count'] / 100  # Normalize
            
            current_processing = current_pos * rule_processing_weight
            optimized_processing = optimized_pos * rule_processing_weight
            
            total_processing_time += current_processing
            optimized_processing_time += optimized_processing
        
        if total_processing_time > 0:
            improvement = ((total_processing_time - optimized_processing_time) / total_processing_time) * 100
            return float(max(improvement, 0))
        else:
            return 0.0