# frontend/app.py
import streamlit as st
from components.false_positive_reduction import *
from components.file_handling import *
from components.rule_conflict_analysis import *
from components.rule_ranking import *
from components.threshold_tuning import *
from styles import * 
from utils import *

# Ensure project root is on sys.path so imports like `supabase_client` work
import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Some helper components are defined in the flat `components.py` file
# (This dynamic import block is kept for completeness)
try:
    from components.threshold_tuning import render_threshold_tuning
except Exception:
    try:
        import importlib.util
        comp_path = os.path.join(os.path.dirname(__file__), 'components.py')
        if os.path.exists(comp_path):
            spec = importlib.util.spec_from_file_location('flat_components', comp_path)
            flat_components = importlib.util.module_from_spec(spec)
            sys.modules['flat_components'] = flat_components
            spec.loader.exec_module(flat_components)
            render_threshold_tuning = getattr(flat_components, 'render_threshold_tuning', None)
    except Exception:
        render_threshold_tuning = None

# -----------------------------
# 1️⃣ Page Config
# -----------------------------
st.set_page_config(
    page_title="WAF Optimizer Pro",
    page_icon="🛡️",
    layout="wide"
)

# 2. Apply Custom Global Styles
apply_custom_styles()

# 4. System Status Check
if check_backend_status():
    pass 
else:
    st.error("🚨 Backend offline - Please run: `python manage.py runserver`")
    st.stop()

# -----------------------------
# 5️⃣ Initialize Session State
# -----------------------------
if 'files_data' not in st.session_state:
    with st.spinner("Loading file library..."):
        st.session_state.files_data = get_files_data()

# 🌟 FIX: Initialize the active tab index and navigation options
TAB_NAMES = [
    " File Management", 
    " Rule Analysis", 
    " Performance", 
    " Rule Ranking", 
    " False Positive Reduction", 
]

if 'active_tab_name' not in st.session_state:
    st.session_state.active_tab_name = TAB_NAMES[0] # Default to the first tab

# ==============================================================================
# MAIN NAVIGATION (st.radio replacement for stable persistence)
# ==============================================================================

# Use st.radio, which is inherently stateful, to replace st.tabs.
selected_tab = st.radio(
    "Navigation", 
    options=TAB_NAMES, 
    index=TAB_NAMES.index(st.session_state.active_tab_name),
    key='main_navigation_radio',
    horizontal=True,
    label_visibility='collapsed'
)

# Update session state immediately (this ensures the selected tab persists 
# even across non-widget-driven reruns)
st.session_state.active_tab_name = selected_tab

# ==============================================================================
# CONDITIONAL RENDERING BASED ON SELECTED TAB
# ==============================================================================

if selected_tab == " File Management":
    # --- TAB 1: FILE MANAGEMENT ---
    st.markdown("### 📂 Workspace & File Management")
    st.markdown("Manage your WAF logs, configuration files, and datasets here.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_file_library()
        st.markdown("---")
        render_file_selection()
        
    with col2:
        render_file_management()
        st.markdown("---")
        render_file_deletion()

elif selected_tab == " Rule Analysis":
    # --- TAB 2: RULE ANALYSIS ---
    st.markdown("###  Deep Rule Analysis")
    st.markdown("Analyze rule conflicts and overlaps within your selected configuration.")
    render_rule_analysis()

elif selected_tab == " Performance":
    # --- TAB 3: PERFORMANCE ---
    st.markdown("###  Performance Profiling")
    st.markdown("Monitor the latency impact and execution time of your WAF rules.")
    
    render_performance_profiling()
    st.markdown("---")
    render_performance_dashboard()

elif selected_tab == " Rule Ranking":
    # --- TAB 4: RULE RANKING ---
    st.markdown("###  Rule Effectiveness Ranking")
    st.markdown("Rank rules based on hit rate, severity, and performance cost.")
    
    render_rule_ranking()
    
    if hasattr(st.session_state, 'current_ranking_session'):
        st.markdown("---")
        st.markdown("#### Ranking Visualization")
        show_ranking_visualization(st.session_state.current_ranking_session)

elif selected_tab == " False Positive Reduction":
    # --- TAB 5: FALSE POSITIVE REDUCTION ---
    render_false_positive_management()

# -----------------------------
# 7️⃣ Footer
# -----------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 0; margin-top: 48px; border-radius: 16px 16px 0 0;">
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 32px; text-align: center;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 16px; margin-bottom: 16px;">
            <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 8px 16px; border-radius: 8px;">
                <span style="color: #ffffff; font-weight: 600; font-size: 16px;">🛡️ WAF Optimizer Pro</span>
            </div>
        </div>
        <div style="color: #a3a3a3; font-size: 14px;">
            <span style="color: #10b981;">Security</span> • 
            <span style="color: #3b82f6;">Performance</span> • 
            <span style="color: #7c3aed;">Intelligence</span>
        </div>
        <div style="color: #737373; font-size: 12px; margin-top: 8px;">
             Intelligent Web Application Firewall Optimization Platform
        </div>
    </div>
</div>
""", unsafe_allow_html=True)