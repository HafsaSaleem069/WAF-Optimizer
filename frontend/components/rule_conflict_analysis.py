import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *
import sys
import os
import datetime # Added datetime import for generating export filename
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.file_handling import render_file_selection

def render_rule_analysis():
    """Render rule analysis section using files from session state"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🔍 Security Analysis</h2>", unsafe_allow_html=True)

    # Check if files are available in session state
    selected_rules = st.session_state.get('selected_rules_file')
    selected_logs = st.session_state.get('selected_logs_file')
    rules_content = st.session_state.get('rules_file_content')
    logs_content = st.session_state.get('logs_file_content')
    
    # Display current file selection status
    if selected_rules and selected_logs:
        st.success("Files ready for analysis!")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Rules File:** {selected_rules['name']}")
        with col2:
            st.info(f"**Logs File:** {selected_logs['name']}")
    else:
        st.warning("Please select files using the global file selection above before running analysis.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    if selected_rules and selected_logs and rules_content and logs_content:
        st.markdown("### Analysis Configuration")
        
        analysis_types = st.multiselect(
            "Select Analysis Types:",
            options=["Shadowing", "Generalization", "Redundancy", "Correlation"],
            default=["Shadowing", "Redundancy"],
            help="Choose which types of rule analysis to perform"
        )
        
        # Map full names to abbreviations
        analysis_map = {
            "Shadowing": "SHD",
            "Generalization": "GEN", 
            "Redundancy": "RXD",
            "Correlation": "COR"
        }
        
        # --- Run Analysis Button Logic ---
        if st.button("Run Security Analysis", type="primary", width='stretch'):
            with st.spinner("Analyzing rule relationships..."):
                # Convert full names to abbreviations before sending
                analysis_types_abbr = [analysis_map[atype] for atype in analysis_types]
                
                # Call the original analyze_rules function with file content
                response = analyze_rules(
                    rules_content, 
                    logs_content, 
                    analysis_types_abbr
                )
                
                if response and response.status_code == 200:
                    st.session_state['analysis_results'] = response.json() # <-- CRITICAL: Store results
                    st.success("✅ Analysis completed!")
                else:
                    st.error("❌ Analysis failed - check backend connection")
        else:
            st.info("👆 Click the button above to start the security analysis with the selected files and analysis types.")
    else:
        st.error("❌ Files are selected but content failed to load. Please try selecting files again.")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # =======================================================
    # --- Persistence Fix: Display results if they exist ---
    # =======================================================
    if 'analysis_results' in st.session_state:
        display_analysis_results(st.session_state['analysis_results'])
    # =======================================================


def display_analysis_results(results):
    """
    Display rule analysis results with enhanced design including AI suggestions 
    and the final export button for the modified CSV.
    """
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Analysis Results")
    
    # Handle different response formats
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Enhanced Metrics Display
    metrics_data = [
        {"label": "Total Rules", "value": data.get('total_rules', 0)},
        {"label": "Relationships", "value": data.get('total_relationships', 0)},
        {"label": "Shadowing", "value": data.get('shd_count', 0)},
        {"label": "Redundant", "value": data.get('rxd_count', 0)},
        
        {"label": "AI Enhanced", "value": "✅" if data.get('ai_available') else "❌"}
    ]
    
    display_enhanced_metrics(metrics_data)
    
    # --- CORRECTED AI CHECK AND ERROR DISPLAY ---
    if data.get('ai_available') is False:
        st.warning("🤖 AI enhancement was not available for this analysis")
        if data.get('ai_error'):
            st.error(f"AI Error: {data.get('ai_error')}")
    # --------------------------------------------
    
    # Relationships
    relationships_data = data.get('relationships', {})
    
    if relationships_data and data.get('total_relationships', 0) > 0:
        st.subheader("🔍 Rule Relationships and Optimization")
        
        # Organized by relationship type (this is the key loop)
        if isinstance(relationships_data, dict):
            for rel_type, rel_list in relationships_data.items():
                if rel_list and isinstance(rel_list, list):
                    st.markdown(f"**{get_relationship_name(rel_type)}**")
                    for rel in rel_list:
                        # --- CORRECT FUNCTION CALL ---
                        display_relationship_item_with_suggestion(rel)
                        # -----------------------------
    
    # Recommendations (General recommendations generated by Python, not Groq)
    recommendations = data.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Optimization Suggestions")
        for rec in recommendations:
            st.write(f"**{rec.get('type', 'Suggestion')}:** {rec.get('description', 'No description')}")
            st.write(f"*Impact:* {rec.get('impact', 'Not specified')}")
            st.markdown("---")
    
    # Show sample rules if available
    sample_rules = data.get('sample_rules', [])
    if sample_rules:
        with st.expander("📋 Sample Rules Analyzed"):
            st.write(f"First {len(sample_rules)} rules: {', '.join(map(str, sample_rules))}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================================================
    # --- NEW: DOWNLOAD BUTTON INTEGRATION (Export Modified CSV) ---
    # This button now correctly appears and is populated with the content 
    # updated by apply_optimization_callback via session state.
    # =========================================================================
    rules_content = st.session_state.get('rules_file_content')
    original_name = st.session_state.get('selected_rules_file', {}).get('name', 'rules')

    if rules_content:
        # Create a dynamic filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"optimized_{original_name.replace('.csv', '')}_{timestamp}.csv"
        
        st.markdown("---")
        st.subheader("⬇️ Export Optimized Rules")
        
        st.download_button(
            label="Download Optimized Rules CSV",
            data=rules_content, 
            file_name=export_filename,
            mime="text/csv",
            type="secondary",
            help="Download the CSV file containing all rules, including applied AI optimizations."
        )
    # =========================================================================



def display_relationship_item_with_suggestion(rel): 
    """Display individual relationship item with its corresponding AI suggestion side-by-side, including an Apply button."""
    rel_type = rel.get('relationship_type', 'UNK')
    rule_a = rel.get('rule_a', 'N/A')
    rule_b = rel.get('rule_b', 'N/A')
    subsuming_rule = rel.get('subsuming_rule')
    subsumed_rule = rel.get('subsumed_rule') 
    
    # Handle different relationship types for the expander title
    if subsuming_rule and subsumed_rule:
        title = f"🔄 Rule {subsuming_rule} subsumes Rule {subsumed_rule} ({rel_type})"
    else:
        title = f"🛡️ Rule {rule_a} vs Rule {rule_b} ({rel_type})"
    
    ai_suggestion = rel.get('ai_suggestion')
    
    # Check if AI data exists to adjust the title tone and set actionability
    action = ai_suggestion.get('action') if ai_suggestion else 'REVIEW_MANUALLY'
    
    # Define which actions warrant an 'Apply' button
    ACTIONABLE_ACTIONS = ['MERGE', 'REMOVE_RULE_A', 'REMOVE_RULE_B', 'REORDER', 'DISABLE', 'UPDATE'] 
    is_actionable = action in ACTIONABLE_ACTIONS

    if is_actionable:
        title = f"✅ {title} → **ACTION:** {action}"
    else:
        # Use existing action or fallback for non-actionable suggestions
        if action not in ['AI_ERROR', 'NO_SUGGESTION', 'REVIEW_MANUALLY', 'KEEP_BOTH']:
             title = f"ℹ️ {title} → **ACTION:** {action}"
        
    # Generate a unique key for the button
    button_key = f"apply_btn_{rule_a}_{rule_b}_{rel_type}" 
    
    # 📌 MODIFICATION 1: Store the relationship data in session state using the unique key
    st.session_state[f'data_{button_key}'] = rel 

    with st.expander(title):
        
        col_detection, col_suggestion = st.columns(2)
        
        # --- LEFT COLUMN: RULE DETECTION DETAILS (Code omitted for brevity) ---
        with col_detection:
            st.markdown("#### 🔍 Rule Detection Details")
            # ... (detection details display) ...
            
        # --- RIGHT COLUMN: AI SUGGESTION DETAILS ---
        with col_suggestion:
            st.markdown("#### 🤖 AI Optimization Suggestion")
            if ai_suggestion:
                # Assume display_ai_suggestion_content handles the nested display
                display_ai_suggestion_content(ai_suggestion)
                
                # Display the APPLY button if the action is actionable
                if is_actionable:
                    st.button(
                        "✨ Apply Suggestion", 
                        key=button_key, 
                        on_click=apply_optimization_callback, 
                        # 📌 MODIFICATION 2: Pass only the unique key in args
                        args=(button_key,) 
                    )
            else:
                st.warning("No AI suggestion generated for this pair.")
                st.info("Review the Rule Detection Details manually.")


def display_ai_suggestion_content(suggestion):
    """Display details of an AI suggestion, designed to be nested inside a column."""
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Action:** `{suggestion.get('action', 'N/A')}`")
        st.write(f"**Security Impact:** {suggestion.get('security_impact', 'N/A')}")
    with col2:
        st.write(f"**Performance:** {suggestion.get('performance_improvement', 'N/A')}")
    
    st.markdown("**Optimized Rule:**")
    st.code(suggestion.get('optimized_rule', 'No rule provided'), language='text')
    
    st.markdown("**Explanation:**")
    st.write(suggestion.get('explanation', 'No explanation provided'))
    
    st.markdown("**Implementation Steps:**")
    steps = suggestion.get('implementation_steps', [])
    if steps:
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")
            
def get_relationship_name(rel_type):
    """Convert relationship type code to readable name"""
    names = {
        'SHD': 'Shadowing Relationships',
        'RXD': 'Redundant Rules', 
        'COR': 'Correlated Rules',
        'SUB': 'Subsumption Relationships',
        'GEN': 'Generalization Relationships'
    }
    return names.get(rel_type, rel_type)

def display_enhanced_metrics(metrics_data):
    """Display metrics with enhanced dark theme design"""
    cols = st.columns(len(metrics_data))
    
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card" style="
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 12px;
                padding: 16px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                transition: transform 0.2s;
            ">
                <div class="metric-value" style="
                    font-size: 26px;
                    font-weight: bold;
                    color: #00C853;
                    margin-bottom: 6px;
                ">{metric['value']}</div>
                <div class="metric-label" style="
                    font-size: 14px;
                    color: #BBBBBB;
                    text-transform: uppercase;
                ">{metric['label']}</div>
            </div>
            """, unsafe_allow_html=True)