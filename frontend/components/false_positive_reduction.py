# false_positive_reduction/component.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *
from components.file_handling import render_file_selection

# --- UI Helpers ---
def section_card_header(title, subtitle):
    """Renders a standard header inside a card."""
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h3 style="color: #ffffff; margin: 0 0 8px 0; font-size: 18px; font-weight: 600; letter-spacing: -0.5px;">{title}</h3>
        <p style="color: #9ca3af; margin: 0; font-size: 14px; line-height: 1.5;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def metric_card(label, value, sub_value=None, border_color="rgba(255,255,255,0.1)"):
    """Renders a styled metric card."""
    sub_html = f'<div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">{sub_value}</div>' if sub_value else ''
    return f"""
    <div style="background: #111318; padding: 20px; border-radius: 12px; border: 1px solid {border_color}; height: 100%;">
        <div style="color: #9ca3af; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
        <div style="color: #ffffff; font-size: 24px; font-weight: 600; margin-top: 8px;">{value}</div>
        {sub_html}
    </div>
    """

# --- Main Management Renderer ---
def render_false_positive_management():
    """FR04: False Positive Reduction Management"""
    st.markdown("""
    <div style="margin-bottom: 32px;">
        <h2 style="background: linear-gradient(135deg, #00ff88, #00d4aa); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   font-size: 28px; font-weight: 600; display: inline-block; margin: 0;">
            False Positive Reduction
        </h2>
        <p style="color: #9ca3af; margin-top: 8px; font-size: 16px;">
            Detect anomalies, analyze traffic patterns, and reduce false alerts to improve WAF accuracy.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Detection & Analysis", "Whitelist Export"])
    with tab1:
        render_false_positive_detection()
    with tab2:
        render_whitelist_export()

# --- Detection & Analysis ---
def render_false_positive_detection():
    """FR04-01: False Positive Detection and Analysis"""
    selected_rules = st.session_state.get('selected_rules_file')
    selected_logs = st.session_state.get('selected_logs_file')
    rules_content = st.session_state.get('rules_file_content')
    logs_content = st.session_state.get('logs_file_content')

    if not selected_rules or not selected_logs or not rules_content or not logs_content:
        st.warning("**Files Required:** Please upload both a Rules file and a Logs file using the global file selection tool.")
        return

    st.success("**Files Ready for Analysis!** Data loaded successfully from session.")
    
    st.markdown(f"""
    <div style="display: flex; gap: 12px; margin-top: 16px; margin-bottom: 24px;">
        <div style="background:#111318; padding:6px 12px; border-radius:12px; color:#10b981;">Rules: {selected_rules['name']}</div>
        <div style="background:#111318; padding:6px 12px; border-radius:12px; color:#10b981;">Logs: {selected_logs['name']}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Run Analysis", key="analyze_fp_btn"):
        with st.spinner("Analyzing traffic patterns..."):
            try:
                response = analyze_false_positives_content_mode(
                    rules_content=rules_content,
                    logs_content=logs_content,
                )
                
                if response is None:
                    st.error("Connection Failed: Could not reach the API server.")
                    return
                
                if not response.content:
                    st.error(f"Empty Response: Server returned status {response.status_code} but no content.")
                    return
                
                try:
                    result = response.json()
                except ValueError as json_err:
                    st.error(f"Invalid JSON Response: {str(json_err)}")
                    return
                
            except Exception as e:
                st.error(f"Request Error: {str(e)}")
                return

        if response.status_code == 200:
            if result.get('status') == 'success':
                if 'session_id' in result:
                    st.session_state.current_fp_session_id = result['session_id']
                
                st.session_state['last_fp_result'] = result
                st.success(f"Analysis Complete! Found {result.get('false_positives_detected', 0)} false positives")
            else:
                st.error(f"Analysis Failed: {result.get('error', 'Unknown error')}")
                return
        else:
            st.error(f"Server Error {response.status_code}: {result.get('error', 'Unknown error')}")
            return

    # Display Results
    if 'last_fp_result' in st.session_state:
        result = st.session_state['last_fp_result']
        false_positives = result.get('false_positives', [])
        whitelist_suggestions = result.get('whitelist_suggestions', [])

        st.markdown('<div style="background:#111318; padding:24px; border-radius:12px; margin-top:16px;">', unsafe_allow_html=True)
        section_card_header("Analysis Results", "Review detected anomalies and suggested whitelists.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(metric_card("Total Detected", len(false_positives)), unsafe_allow_html=True)
        with col2:
            high_risk = len([fp for fp in false_positives if fp.get('false_positive_rate', 0) > 0.3])
            st.markdown(metric_card("High Risk", high_risk, border_color="#ef4444"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card("Suggestions", len(whitelist_suggestions), border_color="#7c3aed"), unsafe_allow_html=True)
        with col4:
            avg_fp_rate = sum(fp.get('false_positive_rate', 0) for fp in false_positives) / len(false_positives) if false_positives else 0
            st.markdown(metric_card("Avg. FP Rate", f"{avg_fp_rate:.1%}"), unsafe_allow_html=True)

        if not false_positives:
            st.info("No False Positives Detected - Your WAF rules appear to be working correctly.")

        if false_positives:
            st.markdown('<h4 style="color: #ffffff; margin: 32px 0 16px 0;">Detected Rules</h4>', unsafe_allow_html=True)
            for fp in false_positives:
                fp_rate = fp.get('false_positive_rate', 0)
                badge_color = "#ef4444" if fp_rate > 0.3 else "#f59e0b" if fp_rate > 0.1 else "#10b981"
                with st.expander(f"Rule {fp.get('rule_id')} - Rate: {fp_rate:.1%}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"""
                        <span style="color:#9ca3af">False Positive Count:</span> <span style="color:#fff">{fp.get('false_positive_count', 0)}</span><br>
                        <span style="color:#9ca3af">Legitimate Requests:</span> <span style="color:#fff">{fp.get('legitimate_request_count', 0)}</span>
                        """, unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <span style="color:#9ca3af">Status:</span> <span style="color:{badge_color}">{fp.get('status', 'detected').title()}</span><br>
                        <span style="color:#9ca3af">Confidence:</span> <span style="color:#fff">{fp.get('confidence_score', 0):.2%}</span>
                        """, unsafe_allow_html=True)

                    if fp.get('blocked_requests'):
                        st.markdown('<div style="margin-top:12px; font-size:13px; color:#9ca3af;">Sample Blocked Requests:</div>', unsafe_allow_html=True)
                        st.dataframe(pd.DataFrame(fp['blocked_requests'][:5]), use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)


# --- Whitelist Export (Updated UI) ---
def render_whitelist_export():
    """FR04-03: Automatic Whitelist Export"""
    
    # Check if analysis has been run
    session_id = st.session_state.get('current_fp_session_id')
    last_result = st.session_state.get('last_fp_result')
    
    if not session_id:
        st.warning("No Analysis Found - Please run a False Positive analysis first from the 'Detection & Analysis' tab.")
        return

    # Container Card matching Analysis Results
    st.markdown('<div class="card" style="background:#111318; padding:24px; border-radius:12px; border:1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
    section_card_header("Whitelist Export", "Generate whitelist configurations from your analysis.")
    
    # Session Info Pill
    st.markdown(f"""
    <div style="display: flex; gap: 12px; margin-bottom: 24px;">
        <div style="background:#1e293b; padding:6px 12px; border-radius:12px; color:#9ca3af; font-size:14px;">
            Session ID: <span style="color:#fff">{session_id}</span>
        </div>
        <div style="background:#1e293b; padding:6px 12px; border-radius:12px; color:#9ca3af; font-size:14px;">
            Suggestions Available: <span style="color:#10b981">{len(last_result.get('whitelist_suggestions', [])) if last_result else 0}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Divider
    st.markdown('<div style="width: 100%; height: 1px; background: rgba(255,255,255,0.1); margin: 24px 0;"></div>', unsafe_allow_html=True)
    
    # Export Configuration
    st.markdown('<p style="color: #ffffff; font-weight: 500; margin-bottom: 12px;">Include Pattern Types</p>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        include_ip = st.checkbox("IP Address", value=False, key="include_ip")
    with c2:
        include_path = st.checkbox("URL Path", value=True, key="include_path")
    with c3:
        include_ua = st.checkbox("User Agent", value=False, key="include_ua")
    with c4:
        include_param = st.checkbox("Parameters", value=False, key="include_param")
    
    # Build include_patterns list
    include_patterns = []
    if include_ip: include_patterns.append("ip_whitelist")
    if include_path: include_patterns.append("path_whitelist")
    if include_ua: include_patterns.append("user_agent_whitelist")
    if include_param: include_patterns.append("parameter_whitelist")
    
    # Auto-generate filename logic (hidden from UI to keep it clean, handled in backend call)
    export_name = f"waf_whitelist_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    if st.button("Generate Whitelist", key="export_whitelist_btn", disabled=not include_patterns):
        with st.spinner("Generating whitelist configuration..."):
            try:
                response = export_whitelist_csv_api(
                    session_id=int(session_id), 
                    export_name=export_name, 
                    include_patterns=include_patterns
                )
                
                if response is None:
                    st.error("Could not connect to API server")
                    return
                
                if response.status_code == 400:
                    error_data = response.json()
                    st.error(f"{error_data.get('error', 'Unknown error')}")
                    return
                
                if response.status_code != 200:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('error', 'Unknown error')}")
                    return
                
                try:
                    result = response.json()
                except ValueError:
                    st.error("Invalid JSON response")
                    return
                
                if result.get('status') == 'success':
                    # Success Display matching standard success style
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 16px; margin-top: 16px;">
                        <h4 style="color: #10b981; margin: 0 0 8px 0; font-size: 16px;">Export Successful</h4>
                        <p style="color: #ffffff; margin: 0; font-size: 14px;">File created successfully.</p>
                        
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Optional: Simple preview table if data exists
                    if last_result and last_result.get('whitelist_suggestions'):
                         st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)
                         with st.expander("View Generated Rules"):
                            sample_data = []
                            for ws in last_result['whitelist_suggestions'][:5]:
                                sample_data.append({
                                    'Type': ws.get('suggestion_type', 'N/A'),
                                    'Description': ws.get('pattern_description', 'N/A'),
                                    'Priority': ws.get('implementation_priority', 'N/A')
                                })
                            st.dataframe(pd.DataFrame(sample_data), use_container_width=True, hide_index=True)

                else:
                    st.error(f"Export error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error during export: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)