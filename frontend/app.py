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
# (not inside the `components` package). Try to import `render_threshold_tuning`
# from the package first, then fall back to loading the top-level `components.py`.
try:
    # Try package-based import (preferred)
    from components.threshold_tuning import render_threshold_tuning
except Exception:
    try:
        # Fallback: dynamic load of the file `frontend/components.py`
        import importlib.util, os, sys
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
# This applies the dark theme, card styles, and typography defined in your styles.py
apply_custom_styles()

# 3. Render the Header
# render_header()

# 4. System Status Check
# Blocks execution if the backend is not reachable
if check_backend_status():
    # Using a subtle toast or container for success to keep UI clean
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

# ==============================================================================
# MAIN NAVIGATION (Horizontal Tabs)
# ==============================================================================

# Define the tabs structure
# We group File operations together, and keep heavy analytical tools in their own tabs
tab_files, tab_analysis, tab_perf, tab_ranking, tab_fp, tab_tuning = st.tabs([
    " File Management", 
    " Rule Analysis", 
    " Performance", 
    " Rule Ranking", 
    " False Positive Reduction", 
    " Threshold Tuning"
])

# --- TAB 1: FILE MANAGEMENT ---
with tab_files:
    st.markdown("### 📂 Workspace & File Management")
    st.markdown("Manage your WAF logs, configuration files, and datasets here.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File Library: Shows currently available files
        render_file_library()
        
        # File Selection: Select active files for analysis
        st.markdown("---")
        render_file_selection()
        
    with col2:
        # File Management: Upload new files
        render_file_management()
        
        # File Deletion: Remove old files
        # Moved here from the bottom of the page for better logical grouping
        st.markdown("---")
        render_file_deletion()

# --- TAB 2: RULE ANALYSIS ---
with tab_analysis:
    st.markdown("###  Deep Rule Analysis")
    st.markdown("Analyze rule conflicts and overlaps within your selected configuration.")
    
    # Render Rule Analysis Component
    render_rule_analysis()

# --- TAB 3: PERFORMANCE ---
with tab_perf:
    st.markdown("###  Performance Profiling")
    st.markdown("Monitor the latency impact and execution time of your WAF rules.")
    
    # Performance Profiling: Setup and run tests
    render_performance_profiling()
    
    st.markdown("---")
    
    # Performance Dashboard: Visual results
    render_performance_dashboard()

# --- TAB 4: RULE RANKING ---
with tab_ranking:
    st.markdown("###  Rule Effectiveness Ranking")
    st.markdown("Rank rules based on hit rate, severity, and performance cost.")
    
    # Render Ranking Controls
    render_rule_ranking()
    
    # Conditional Rendering: Ranking Visualization
    # Only shows if a ranking session has been generated
    if hasattr(st.session_state, 'current_ranking_session'):
        st.markdown("---")
        st.markdown("#### Ranking Visualization")
        show_ranking_visualization(st.session_state.current_ranking_session)

# --- TAB 5: FALSE POSITIVE REDUCTION ---
with tab_fp:
    # Render FR04 False Positive Reduction Component
    render_false_positive_management()

# --- TAB 6: THRESHOLD TUNING ---
with tab_tuning:
    st.markdown("### Anomaly Threshold Tuning")
    st.markdown("Fine-tune sensitivity thresholds for anomaly detection rules.")
    
    # Render Threshold Tuning Component
    render_threshold_tuning()

# File deletion
render_file_deletion()

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
