import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

class RankingVisualizer:
    """
    FR05-02: Visualize current vs proposed ranking
    LEARNING: Helps users understand the changes before applying them
    """
    
    def create_ranking_comparison_chart(self, current_ranking: List, optimized_ranking: List):
        """
        FR05-02: Show side-by-side comparison
        LEARNING: Visual proof that the new order is better
        """
        # Prepare data for visualization
        comparison_data = []
        
        for rule in optimized_ranking:
            comparison_data.append({
                'rule_id': rule['rule_id'],
                'current_position': rule['current_position'],
                'new_position': rule['new_position'],
                'hit_count': rule['hit_count'],
                'priority_score': rule['priority_score'],
                'movement': '⬆️ Improved' if rule['new_position'] < rule['current_position'] else '⬇️ Demoted'
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Create comparison scatter plot
        fig = px.scatter(
            df, 
            x='current_position', 
            y='new_position',
            size='hit_count',
            color='movement',
            hover_data=['rule_id', 'priority_score'],
            title='FR05-02: Current vs Proposed Rule Positions<br>Size = Hit Count'
        )
        
        # Add perfect line (where current = new)
        fig.add_trace(
            go.Scatter(
                x=[1, len(current_ranking)],
                y=[1, len(current_ranking)], 
                mode='lines',
                line=dict(dash='dash', color='gray'),
                name='No Change'
            )
        )
        
        fig.update_layout(
            xaxis_title='Current Position (Higher = Checked Later)',
            yaxis_title='Proposed Position (Higher = Checked Later)',
            showlegend=True
        )
        
        return fig
    
    def create_performance_gain_chart(self, improvement_metrics: Dict):
        """
        FR05-04: Show expected performance improvements
        LEARNING: Quantifies the benefits of reordering
        """
        metrics = {
            'Estimated Speed Improvement': improvement_metrics.get('speed_improvement', 0),
            'Reduced Average Checks': improvement_metrics.get('reduced_checks', 0),
            'CPU Usage Reduction': improvement_metrics.get('cpu_reduction', 0)
        }
        
        fig = px.bar(
            x=list(metrics.keys()),
            y=list(metrics.values()),
            title='FR05-04: Expected Performance Improvements',
            labels={'x': 'Metric', 'y': 'Improvement (%)'}
        )
        
        fig.update_traces(marker_color='green')
        
        return fig