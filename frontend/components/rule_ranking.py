import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

def render_performance_profiling():
    """FR03: Performance Profiling Section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Performance Profiling")
    st.write("Analyze rule efficiency and identify optimization opportunities")
    
    def _normalize(f, default_type='traffic'):
        filename = f.get('filename') or f.get('name') or f.get('file') or f.get('file_name') or f.get('key') or f.get('path') or ''
        _id = f.get('id') or f.get('supabase_path') or filename
        file_type = f.get('file_type') or default_type
        return {'id': _id, 'filename': filename, 'file_type': file_type, 'raw': f}

    col1, col2 = st.columns(2)
    with col1:
        files_data = st.session_state.get('files_data', [])
        traffic_files = [ _normalize(f, 'traffic') for f in files_data if (f.get('file_type') or '').lower() == 'traffic' ]

        # fallback to any selected session value if backend list is empty
        sel_traffic = st.session_state.get('selected_logs_file') or st.session_state.get('selected_traffic_file') or st.session_state.get('selected_traffic')
        if not traffic_files and sel_traffic:
            traffic_files = [_normalize(sel_traffic, 'traffic')]

        # build default index from session state selection
        default_index = 0
        if sel_traffic and traffic_files:
            sel_name = sel_traffic.get('filename') or sel_traffic.get('name') or sel_traffic.get('file')
            for i, t in enumerate(traffic_files):
                if t['filename'] and sel_name and t['filename'].endswith(sel_name.split('/')[-1]):
                    default_index = i
                    break

        selected_traffic = st.selectbox(
            "Select Traffic Data:",
            options=traffic_files,
            format_func=lambda x: (x.get('filename') or '').split('/')[-1],
            index=default_index,
            key="performance_traffic_select"
        )
    with col2:
        snapshot_name = st.text_input("Analysis Name:", "Performance Analysis", key="snapshot_name")
    
    if st.button("🔍 Analyze Rule Performance", type="primary", key="analyze_performance"):
        if selected_traffic:
            with st.spinner("🔄 Analyzing rule performance patterns..."):
                response = update_performance_data()
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # Show summary
                    summary = result['summary']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Requests", summary['total_requests'])
                    with col2:
                        st.metric("Rules Triggered", summary['rules_triggered'])
                    with col3:
                        st.metric("Hits Updated", summary['hits_updated'])
                    with col4:
                        st.metric("Metrics Calculated", summary['metrics_calculated'])
                    
                    # Show flagged rules
                    flagged = result.get('flagged_rules', {})
                    if flagged:
                        st.subheader("🚩 Flagged Rules")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if flagged.get('rarely_used'):
                                st.metric("Rarely Used", len(flagged['rarely_used']), delta="Optimize")
                        with col2:
                            if flagged.get('redundant'):
                                st.metric("Redundant", len(flagged['redundant']), delta="Review")
                        with col3:
                            if flagged.get('high_performance'):
                                st.metric("High Performers", len(flagged['high_performance']), delta="Excellent")
                        
                        # Show details of flagged rules
                        with st.expander("View Flagged Rule Details"):
                            for category, rules in flagged.items():
                                if rules:
                                    st.write(f"**{category.upper().replace('_', ' ')}:**")
                                    for rule in rules:
                                        st.write(f"- {rule['rule_id']}: {rule.get('reason', 'No reason provided')}")
                    
                    # Show performance metrics
                    metrics = result.get('performance_metrics', {})
                    if metrics:
                        st.subheader("📈 Performance Metrics")
                        metrics_df = pd.DataFrame.from_dict(metrics, orient='index').reset_index()
                        metrics_df.columns = ['Rule ID', 'Match Frequency', 'Effectiveness Ratio', 'Hit Count']
                        metrics_df['Match Frequency'] = metrics_df['Match Frequency'].apply(lambda x: f"{x:.2%}")
                        metrics_df['Effectiveness Ratio'] = metrics_df['Effectiveness Ratio'].apply(lambda x: f"{x:.1%}")
                        st.dataframe(metrics_df, width='stretch')
                        
                else:
                    st.error("❌ Performance analysis failed")
        else:
            st.warning("Please select traffic data for analysis")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_performance_dashboard():
    """Show performance dashboard"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📈 Performance Dashboard")
    
    response = get_performance_dashboard()
    if response and response.status_code == 200:
        dashboard_data = response.json()
        
        # Overview metrics
        metrics = dashboard_data['summary']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rules", metrics['total_rules_tracked'])
        with col2:
            st.metric("Total Hits", metrics['total_hits_recorded'])
        with col3:
            st.metric("Avg Hits/Rule", f"{metrics['average_hits_per_rule']:.1f}")
        with col4:
            flagged = metrics.get('flagged_rules_summary', {})
            st.metric("Optimization Opportunities", flagged.get('rarely_used', 0) + flagged.get('redundant', 0))
        
        # Top performers
        top_rules = dashboard_data.get('top_performing_rules', [])
        if top_rules:
            st.subheader("🏆 Top Performing Rules")
            perf_df = pd.DataFrame(top_rules)
            st.dataframe(perf_df, width='stretch')
        
        # All rules with metrics
        all_rules = dashboard_data.get('all_rules', [])
        if all_rules:
            with st.expander("View All Rule Performance Data"):
                rules_df = pd.DataFrame(all_rules)
                # Format percentages for better display
                if 'match_frequency' in rules_df.columns:
                    rules_df['match_frequency'] = rules_df['match_frequency'].apply(
                        lambda x: f"{float(x):.2%}" if x else "0%"
                    )
                if 'effectiveness_ratio' in rules_df.columns:
                    rules_df['effectiveness_ratio'] = rules_df['effectiveness_ratio'].apply(
                        lambda x: f"{float(x):.1%}" if x else "0%"
                    )
                st.dataframe(rules_df, width='stretch')
    else:
        st.error("Error loading dashboard")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_rule_ranking():
    """Rule Ranking Section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("⚡ Performance Optimization")
    st.write("Intelligent rule reordering based on performance data")
    
    def _normalize(f, default_type='rules'):
        filename = f.get('filename') or f.get('name') or f.get('file') or f.get('file_name') or f.get('key') or f.get('path') or ''
        _id = f.get('id') or f.get('supabase_path') or filename
        file_type = f.get('file_type') or default_type
        return {'id': _id, 'filename': filename, 'file_type': file_type, 'raw': f}

    col1, col2 = st.columns(2)
    with col1:
        files_data = st.session_state.get('files_data', [])
        rules_files = [ _normalize(f, 'rules') for f in files_data if (f.get('file_type') or '').lower() == 'rules' ]

        # fallback to any selected session value if backend list is empty
        sel_rules = st.session_state.get('selected_rules_file') or st.session_state.get('selected_rules')
        if not rules_files and sel_rules:
            rules_files = [_normalize(sel_rules, 'rules')]

        # default selection index based on session state
        default_index = 0
        if sel_rules and rules_files:
            sel_name = sel_rules.get('filename') or sel_rules.get('name') or sel_rules.get('file')
            for i, r in enumerate(rules_files):
                if r['filename'] and sel_name and r['filename'].endswith(sel_name.split('/')[-1]):
                    default_index = i
                    break

        selected_rules = st.selectbox(
            "Select Rules Configuration:",
            options=rules_files,
            format_func=lambda x: (x.get('filename') or '').split('/')[-1],
            index=default_index,
            key="ranking_rules_select"
        )
    with col2:
        session_name = st.text_input("Session Name:", "Optimization Analysis", key="session_name")
    
    if st.button("🚀 Generate Optimized Ranking", type="primary", key="generate_ranking"):
        if selected_rules:
            with st.spinner("🔄 Analyzing and optimizing rule order..."):
                response = generate_rule_ranking(selected_rules['id'], session_name)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Performance Gain", f"{result['improvement']}%")
                    with col2:
                        st.metric("Rules Processed", result['rules_analyzed'])
                    with col3:
                        st.metric("Session ID", result['session_id'])
                    
                    st.session_state.current_ranking_session = result['session_id']
                else:
                    st.error("❌ Optimization failed")
        else:
            st.warning("Please select a rules configuration")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ranking_visualization(session_id):
    """Enhanced ranking visualization"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📈 Optimization Results")
    
    try:
        response = get_ranking_comparison(session_id)
        if response and response.status_code == 200:
            comparison_data = response.json()
            
            # Enhanced metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Performance Gain", f"{comparison_data['improvement']:.1f}%")
            with col2:
                st.metric("Rules Improved", comparison_data['summary']['rules_moved_up'])
            with col3:
                st.metric("Rules Adjusted", comparison_data['summary']['rules_moved_down'])
            with col4:
                st.metric("Avg Change", f"{comparison_data['summary']['average_position_change']:+.1f}")
            
            if comparison_data['comparison_data']:
                df = pd.DataFrame(comparison_data['comparison_data'])
                
                # Enhanced visualization
                fig = px.scatter(
                    df,
                    x='current_position',
                    y='proposed_position',
                    size='hit_count',
                    color='position_change',
                    hover_data=['rule_id', 'priority_score', 'category'],
                    title='Rule Position Optimization',
                    labels={
                        'current_position': 'Current Position',
                        'proposed_position': 'Optimized Position',
                        'position_change': 'Improvement',
                        'hit_count': 'Usage Frequency'
                    }
                )
                
                max_pos = max(df['current_position'].max(), df['proposed_position'].max())
                fig.add_trace(px.line(x=[1, max_pos], y=[1, max_pos]).data[0])
                fig.data[-1].line.dash = 'dash'
                fig.data[-1].line.color = '#94a3b8'
                fig.data[-1].name = 'Reference'
                
                st.plotly_chart(fig, width='stretch')
                
                st.info(f"💡 **Performance Insight:** Optimized rule order can improve processing speed by approximately {comparison_data['improvement']:.1f}%")
                
                # Add detailed table view of reordered rules
                st.subheader("📋 Detailed Rule Reordering")
                
                # Create display dataframe with better formatting
                display_df = df.copy()
                display_df = display_df.sort_values('proposed_position')
                display_df['Position Change'] = display_df['position_change'].apply(
                    lambda x: f"↑ {abs(x)}" if x > 0 else (f"↓ {abs(x)}" if x < 0 else "→ 0")
                )
                display_df['Status'] = display_df.apply(
                    lambda row: '🔥 High Performance' if row.get('is_high_performance', False) 
                    else ('⚠️ Rarely Used' if row.get('is_rarely_used', False) else '✓ Normal'),
                    axis=1
                )
                
                # Select and rename columns for display
                columns_to_show = {
                    'rule_id': 'Rule ID',
                    'current_position': 'Original Position',
                    'proposed_position': 'New Position',
                    'Position Change': 'Change',
                    'hit_count': 'Hit Count',
                    'priority_score': 'Priority Score',
                    'category': 'Category',
                    'Status': 'Status'
                }
                
                # Filter to only include columns that exist
                existing_columns = [col for col in columns_to_show.keys() if col in display_df.columns]
                table_df = display_df[existing_columns].rename(columns=columns_to_show)
                
                st.dataframe(
                    table_df,
                    width='stretch',
                    height=400
                )
                
                # Add download button for the ranking
                csv = table_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Optimized Rule Order",
                    data=csv,
                    file_name=f"optimized_rules_session_{session_id}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Error loading visualization: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    st.markdown('</div>', unsafe_allow_html=True)
