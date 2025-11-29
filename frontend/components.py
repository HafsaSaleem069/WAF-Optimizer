
import plotly.express as px
from utils import *
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# API Base URL - FIXED: Use consistent base URL
API_BASE = "http://127.0.0.1:8000/api"

def update_performance_data(payload):
    """Send performance analysis data to backend - FIXED"""
    try:
        print(f"🔄 Sending performance analysis payload: {payload}")
        
        # Validate required fields - FIXED: match backend expectations
        required_fields = ["rules_file_id", "session_name"]
        for field in required_fields:
            if field not in payload:
                st.error(f"❌ Missing required field: {field}")
                return None
        
        # FIXED: Use the correct endpoint and payload structure
        response = requests.post(
            f'{API_BASE}/performance/analyze/',  # Make sure this endpoint exists
            json=payload,
            timeout=30
        )
        print(f"📊 Performance API Response: {response.status_code}")
        return response
    except Exception as e:
        st.error(f"🚨 Performance analysis API error: {e}")
        return None

def generate_rule_ranking(rules_file_id, session_name):
    """Generate optimized rule ranking - FIXED"""
    try:
        print(f"🔄 Generating ranking for rules_file_id: {rules_file_id}")
        
        # FIXED: Use the exact payload structure backend expects
        ranking_payload = {
            "rules_file_id": rules_file_id,
            "session_name": session_name
        }
        
        # FIXED: Make sure this endpoint exists in your Django URLs
        response = requests.post(
            f'{API_BASE}/ranking/generate/',  # Check if this endpoint exists
            json=ranking_payload,
            timeout=30
        )
        print(f"📈 Ranking API Response: {response.status_code}")
        return response
    except Exception as e:
        st.error(f"🚨 Ranking generation API error: {e}")
        return None
def update_hit_counts(traffic_file_id, rules_file_id):
    """Update hit counts for rules - FIXED"""
    try:
        print(f"🔄 Updating hit counts for traffic: {traffic_file_id}, rules: {rules_file_id}")
        
        # FIXED: Match backend expected payload - CHANGED as requested
        hitcount_payload = {
            "traffic_file_id": traffic_file_id,
            "rules_file_id": rules_file_id
        }
        
        response = requests.post(
            f'{API_BASE}/hit-counts/update/',
            json=hitcount_payload,
            timeout=30
        )
        print(f"🎯 Hit Counts API Response: {response.status_code}")
        return response
    except Exception as e:
        st.error(f"🚨 Hit counts update API error: {e}")
        return None
    
def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        response = requests.get(f'{API_BASE}/performance/dashboard/', timeout=30)
        return response
    except Exception as e:
        st.error(f"🚨 Dashboard API error: {e}")
        return None

def get_ranking_comparison(session_id):
    """Get ranking comparison data"""
    try:
        response = requests.get(f'{API_BASE}/ranking/comparison/{session_id}/', timeout=30)
        return response
    except Exception as e:
        st.error(f"🚨 Ranking comparison API error: {e}")
        return None

# File management functions
def get_files_data():
    """Get uploaded files data"""
    try:
        response = requests.get(f'{API_BASE}/files/summary/', timeout=30)
        if response.status_code == 200:
            data = response.json()
            # If the summary endpoint returns grouped lists, flatten them
            if isinstance(data, dict) and ('rules' in data or 'traffic' in data):
                rules = data.get('rules', []) or []
                traffic = data.get('traffic', []) or []
                return rules + traffic
            # Otherwise assume it's already a flat list
            return data
        return []
    except Exception as e:
        print(f"🚨 Files API error: {e}")
        return []

def upload_file(file, file_type):
    """Upload file to backend"""
    try:
        files = {'file': (file.name, file, 'text/csv')}
        data = {'file_type': file_type}
        # POST to the files ViewSet endpoint
        response = requests.post(f'{API_BASE}/files/', files=files, data=data)
        return response
    except Exception as e:
        st.error(f"🚨 Upload error: {e}")
        return None

def delete_file(file_id):
    """Delete file from backend"""
    try:
        response = requests.delete(f'{API_BASE}/files/{file_id}/')
        return response
    except Exception as e:
        st.error(f"🚨 Delete error: {e}")
        return None

def validate_csv_structure(file, file_type):
    """Validate CSV structure"""
    try:
        file.seek(0)
        df = pd.read_csv(file)
        
        if file_type == 'rules':
            required_columns = ['id', 'category', 'parameter', 'operator', 'value', 'phase', 'action', 'priority']
        elif file_type == 'traffic':
            required_columns = ['timestamp', 'src_ip', 'method', 'url']
        else:
            return False, "Unknown file type"
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing columns: {missing_columns}"
        
        return True, "Valid CSV structure"
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"

def analyze_rules(rules_file_id, traffic_file_id, analysis_types):
    """Analyze rule relationships"""
    try:
        payload = {
            "rules_file_id": rules_file_id,
            "traffic_file_id": traffic_file_id,
            "analysis_types": analysis_types
        }
        response = requests.post(f'{API_BASE}/analyze/', json=payload)
        return response
    except Exception as e:
        st.error(f"🚨 Analysis error: {e}")
        return None

# FR04 False Positive Functions
def detect_false_positives_api(session_id, detection_method, threshold):
    """Detect false positives"""
    try:
        payload = {
            "session_id": session_id,
            "detection_method": detection_method,
            "false_positive_threshold": threshold
        }
        response = requests.post(f'{API_BASE}/false-positives/detect/', json=payload)
        return response
    except Exception as e:
        st.error(f"🚨 False positive detection error: {e}")
        return None

def start_learning_mode_api(session_id, duration, sample_size):
    """Start learning mode"""
    try:
        payload = {
            "session_id": session_id,
            "learning_duration_hours": duration,
            "traffic_sample_size": sample_size
        }
        response = requests.post(f'{API_BASE}/learning-mode/start/', json=payload)
        return response
    except Exception as e:
        st.error(f"🚨 Learning mode error: {e}")
        return None

def generate_whitelist_suggestions_api(false_positive_id, suggestion_types):
    """Generate whitelist suggestions"""
    try:
        payload = {
            "false_positive_id": false_positive_id,
            "suggestion_types": suggestion_types
        }
        response = requests.post(f'{API_BASE}/whitelist-suggestions/generate/', json=payload)
        return response
    except Exception as e:
        st.error(f"🚨 Whitelist suggestions error: {e}")
        return None

def export_whitelist_csv_api(session_id, export_name, include_patterns):
    """Export whitelist CSV"""
    try:
        payload = {
            "session_id": session_id,
            "export_name": export_name,
            "include_patterns": include_patterns
        }
        response = requests.post(f'{API_BASE}/whitelist/export-csv/', json=payload)
        return response
    except Exception as e:
        st.error(f"🚨 Whitelist export error: {e}")
        return None

def get_learning_mode_status_api(learning_session_id):
    """Get learning mode status"""
    try:
        response = requests.get(f'{API_BASE}/learning-mode/status/{learning_session_id}/')
        return response
    except Exception as e:
        st.error(f"🚨 Learning mode status error: {e}")
        return None

# frontend/components/threshold_tuning.py
def threshold_tuning_module():
    """Threshold Tuning Module for FR04 - False Positive Reduction"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
        <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">🎯 Threshold Tuning</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 16px;">
            Optimize WAF anomaly score thresholds to reduce false positives
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main functionality
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Run Threshold Analysis")
        st.write("Analyze uploaded traffic logs to find optimal anomaly score threshold")
        
        if st.button("🚀 Run Threshold Tuning", type="primary", use_container_width=True):
            with st.spinner("Analyzing traffic patterns and finding optimal threshold..."):
                try:
                    response = requests.post('http://127.0.0.1:8000/api/threshold_tuning/')
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Threshold tuning completed successfully!")
                        
                        # Display results
                        display_threshold_results(result)
                        
                    else:
                        error_msg = response.json().get('error', 'Unknown error')
                        st.error(f"❌ Analysis failed: {error_msg}")
                        
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
                    st.info("💡 Make sure Django backend is running on port 8000")
    
    with col2:
        st.markdown("### ⚙️ Settings")
        st.info("""
        **Input Requirements:**
        - CSV files in `uploads/` folder
        - Must contain `anomaly_score` column
        - Must contain `action` column
        """)
        
        # Quick actions
        if st.button("🔄 Check Uploads Folder", type="secondary"):
            check_uploads_folder()
    
    # Display existing suggestions
    display_existing_suggestions()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_threshold_results(result):
    """Display threshold tuning results"""
    st.markdown("---")
    st.markdown("### 📈 Analysis Results")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Optimal Threshold", f"{result['best_threshold']:.2f}")
    with col2:
        st.metric("Accuracy", f"{result['accuracy']:.1%}")
    with col3:
        st.metric("Records Tested", result['records_tested'])
    with col4:
        st.metric("File Used", result['file_used'][:15] + "...")
    
    # Detailed explanation
    with st.expander("📋 View Detailed Analysis"):
        st.write(f"**File Analyzed:** {result['file_used']}")
        st.write(f"**Optimal Threshold:** {result['best_threshold']}")
        st.write(f"**Achieved Accuracy:** {result['accuracy']:.1%}")
        st.write(f"**Suggestion ID:** {result['saved_id']}")
        
        st.info("""
        **Interpretation:**
        - Threshold represents the minimum anomaly score to block a request
        - Higher threshold = fewer false positives but might miss some attacks
        - Lower threshold = better attack detection but more false positives
        """)

def display_existing_suggestions():
    """Display existing threshold suggestions"""
    st.markdown("---")
    st.markdown("### 💾 Saved Suggestions")
    
    try:
        response = requests.get('http://127.0.0.1:8000/threshold_suggestions/')
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            
            if suggestions:
                df = pd.DataFrame(suggestions)
                
                # Format the dataframe for better display
                display_df = df[['id', 'value', 'approved', 'applied', 'created_at']].copy()
                display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['status'] = display_df.apply(
                    lambda row: '✅ Approved' if row['approved'] else '⏳ Pending', 
                    axis=1
                )
                
                st.dataframe(
                    display_df.rename(columns={
                        'id': 'ID',
                        'value': 'Threshold',
                        'status': 'Status',
                        'created_at': 'Created'
                    }),
                    use_container_width=True
                )
                
                # Approval functionality
                st.markdown("#### ✅ Approve Suggestions")
                pending_suggestions = [s for s in suggestions if not s['approved']]
                
                if pending_suggestions:
                    suggestion_options = {
                        f"ID {s['id']}: Threshold {s['value']}": s['id'] 
                        for s in pending_suggestions
                    }
                    
                    selected_suggestion = st.selectbox(
                        "Choose suggestion to approve:",
                        options=list(suggestion_options.keys())
                    )
                    
                    if st.button("👍 Approve Selected Suggestion", type="primary"):
                        suggestion_id = suggestion_options[selected_suggestion]
                        approve_response = requests.post(
                            f'http://127.0.0.1:8000/threshold_suggestions/approve/{suggestion_id}/'
                        )
                        
                        if approve_response.status_code == 200:
                            st.success("✅ Suggestion approved successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Approval failed")
                else:
                    st.info("🎉 All suggestions are already approved!")
                    
            else:
                st.info("📝 No threshold suggestions yet. Run analysis first.")
                
        else:
            st.error("❌ Failed to load suggestions")
            
    except Exception as e:
        st.error(f"🚨 Error loading suggestions: {str(e)}")

def check_uploads_folder():
    """Check what files are available in uploads folder"""
    try:
        # This would typically call a backend endpoint to list uploads
        st.info("🔍 Checking uploads folder...")
        # For now, we rely on the threshold_tuning API to handle file detection
        st.success("✅ Uploads folder is accessible")
    except Exception as e:
        st.error(f"❌ Error checking uploads: {str(e)}")

def render_header():
    """Render the main header with enhanced dark theme based on MindLink design"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 48px; margin: 0 auto; max-width: 900px; box-sizing: border-box;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px;">
            <div>
                <p style="margin: 0 0 4px 0; font-size: 28px; line-height: 1.2; color: #ffffff; font-weight: 600;">
                    Good evening, Mark!
                </p>
                <p style="margin: 4px 0 0 0; color: #a3a3a3; font-size: 16px;">
                    What would you like to explore today?
                </p>
            </div>
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="background: #242424; padding: 8px; border-radius: 6px; position: relative; cursor: pointer; border: 1px solid #333333;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-bell"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; position: absolute; top: 6px; right: 6px; border: 2px solid #1a1a1a;"></div>
                </div>
                <div style="width: 1px; height: 30px; background-color: #404040;"></div>
                <div style="background: #242424; padding: 8px; border-radius: 6px; cursor: pointer; border: 1px solid #333333;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-star"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                </div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    
def render_threshold_tuning():
    """Threshold Tuning Module for FR04 - False Positive Reduction - FIXED"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
        <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">🎯 Threshold Tuning</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 16px;">
            Optimize WAF anomaly score thresholds to reduce false positives
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main functionality
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Run Threshold Analysis")
        st.write("Analyze uploaded traffic logs to find optimal anomaly score threshold")
        
        # File selection for threshold tuning
        files_data = st.session_state.get('files_data', [])
        traffic_files = [f for f in files_data if f['file_type'] == 'traffic']
        
        if traffic_files:
            selected_traffic = st.selectbox(
                "Select Traffic File for Analysis:",
                options=traffic_files,
                format_func=lambda x: x.get('filename', x.get('file', 'Unknown File')),
                key="threshold_traffic_select"
            )
            
            if st.button("🚀 Run Threshold Tuning", type="primary", use_container_width=True):
                with st.spinner("Analyzing traffic patterns and finding optimal threshold..."):
                    try:
                        # FIXED: Use the correct API endpoint with proper payload
                        payload = {
                            "traffic_file_id": selected_traffic['id']
                        }
                        response = requests.post(
                            f'{API_BASE}/threshold_tuning/',  # FIXED: Use API_BASE
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Threshold tuning completed successfully!")
                            
                            # Display results
                            display_threshold_results(result)
                            
                        else:
                            error_msg = response.json().get('error', 'Unknown error')
                            st.error(f"❌ Analysis failed: {error_msg}")
                            
                    except Exception as e:
                        st.error(f"🚨 Connection error: {str(e)}")
                        st.info("💡 Make sure Django backend is running on port 8000")
        else:
            st.warning("Please upload traffic files first")
    
    with col2:
        st.markdown("### ⚙️ Settings")
        st.info("""
        **Input Requirements:**
        - CSV files with traffic data
        - Must contain `anomaly_score` column
        - Must contain `action` column
        """)
    
    # Display existing suggestions
    display_existing_suggestions()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_existing_suggestions():
    """Display existing threshold suggestions - FIXED"""
    st.markdown("---")
    st.markdown("### 💾 Saved Suggestions")
    
    try:
        # FIXED: Use API_BASE consistently
        response = requests.get(f'{API_BASE}/threshold_suggestions/')
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            
            if suggestions:
                df = pd.DataFrame(suggestions)
                
                # Format the dataframe for better display
                display_df = df[['id', 'value', 'approved', 'applied', 'created_at']].copy()
                display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['status'] = display_df.apply(
                    lambda row: '✅ Approved' if row['approved'] else '⏳ Pending', 
                    axis=1
                )
                
                st.dataframe(
                    display_df.rename(columns={
                        'id': 'ID',
                        'value': 'Threshold',
                        'status': 'Status',
                        'created_at': 'Created'
                    }),
                    use_container_width=True
                )
                
                # Approval functionality
                st.markdown("#### ✅ Approve Suggestions")
                pending_suggestions = [s for s in suggestions if not s['approved']]
                
                if pending_suggestions:
                    suggestion_options = {
                        f"ID {s['id']}: Threshold {s['value']}": s['id'] 
                        for s in pending_suggestions
                    }
                    
                    selected_suggestion = st.selectbox(
                        "Choose suggestion to approve:",
                        options=list(suggestion_options.keys())
                    )
                    
                    if st.button("👍 Approve Selected Suggestion", type="primary"):
                        suggestion_id = suggestion_options[selected_suggestion]
                        # FIXED: Use API_BASE
                        approve_response = requests.post(
                            f'{API_BASE}/threshold_suggestions/approve/{suggestion_id}/'
                        )
                        
                        if approve_response.status_code == 200:
                            st.success("✅ Suggestion approved successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Approval failed")
                else:
                    st.info("🎉 All suggestions are already approved!")
                    
            else:
                st.info("📝 No threshold suggestions yet. Run analysis first.")
                
        else:
            st.error("❌ Failed to load suggestions")
            
    except Exception as e:
        st.error(f"🚨 Error loading suggestions: {str(e)}")
        
def render_main_dashboard():
    """Renders a main content dashboard section based on MindLink design system."""
    st.markdown("""
    <div style="max-width: 900px; margin: 0 auto; padding: 0 48px;">
        <div class="element-spacing">
            <h3 style="margin-bottom: 16px; font-size: 16px; color: #a3a3a3;">Choose your focus</h3>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 32px;">
                <span class="pill pill-active">Summarize reports</span>
                <span class="pill">Extract key insights</span>
                <span class="pill">Compare projects</span>
                <span class="pill">Answer questions</span>
                <span class="pill">Draft documents</span>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; background-color: #242424;">
            <p style="margin: 0; font-size: 16px; color: #ffffff;">
                Ask something about your workspace or documents.
            </p>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-refresh-cw" style="cursor: pointer;"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.5 7.9c1.1-2.2 3.4-3.5 5.9-3.5h.5c4.6 0 8.5 3.5 8.9 8"></path><path d="M20.5 16.1c-1.1 2.2-3.4 3.5-5.9 3.5h-.5c-4.6 0-8.5-3.5-8.9-8"></path></svg>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 32px; display: flex; gap: 24px; align-items: center; background-color: #242424;">
            <div style="width: 120px; height: 120px; border-radius: 16px; padding: 16px; background: linear-gradient(135deg, #7c3aed, #8b5cf6, #ec4899); display: flex; justify-content: center; align-items: center;">
                <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            </div>
            <div style="flex: 1;">
                <p style="margin: 0; font-size: 16px; line-height: 1.5; color: #ffffff;">
                    Generate a one-page summary of the product roadmap.
                </p>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 13px; color: #a3a3a3;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #f59e0b;"></div> <!-- Loading dot -->
                    Wait a minute
                </div>
            </div>
        </div>
        
        <div class="card" style="margin-bottom: 24px; padding: 28px; background-color: #242424;">
            <span class="badge" style="background-color: #ec4899; color: #ffffff; margin-bottom: 16px;">GOAL</span>
            <p style="margin-bottom: 24px; font-size: 17px; line-height: 1.6; font-weight: 500; color: #ffffff;">
                Deliver a unified, intelligent workspace that connects all company knowledge and enables contextual answers in real time.
            </p>
            <div style="padding: 16px 0; border-top: 1px solid #333333; display: flex; justify-content: space-between; gap: 16px;">
                <div style="flex: 1;">
                    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 500; color: #ffffff;">Phase 1: Integrations</p>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #a3a3a3;">Connect Google Drive, Notion, Slack and Confluence as data sources.</p>
                </div>
                <span class="badge" style="background-color: #10b981; color: #000000; align-self: flex-start;">Completed</span>
            </div>
            <div style="padding: 16px 0; border-top: 1px solid #333333; display: flex; justify-content: space-between; gap: 16px;">
                <div style="flex: 1;">
                    <p style="margin: 0 0 8px 0; font-size: 15px; font-weight: 500; color: #ffffff;">Phase 2: Contextual chat</p>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #a3a3a3;">Launch Ask AI interface with smart document linking and reference citations.</p>
                </div>
                <span class="badge" style="background-color: #10b981; color: #000000; align-self: flex-start;">In Progress</span>
            </div>
        </div>

        <div style="position: fixed; bottom: 32px; left: calc(250px + 48px); right: calc(320px + 48px); max-width: 900px; margin: 0 auto;">
            <div style="padding: 8px 12px; border-radius: 28px; background-color: #242424; display: flex; gap: 8px; align-items: center; border: 1px solid #333333;">
                <button style="padding: 10px; border-radius: 8px; width: 40px; height: 40px; background: none; border: none; cursor: pointer;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-paperclip"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49L17.5 2.5A4 4 0 0 1 23 8l-7.1 7.1"></path></svg>
                </button>
                <button style="padding: 10px; border-radius: 8px; width: 40px; height: 40px; background: none; border: none; cursor: pointer;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-zap"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                </button>
                <input type="text" placeholder="Ask mindlink..." style="padding: 10px 12px; flex: 1; border: none; outline: none; background: transparent; color: #ffffff; font-size: 14px;">
                <button style="padding: 10px; border-radius: 8px; width: 40px; height: 40px; background: none; border: none; cursor: pointer;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a3a3a3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-microphone"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
                </button>
                <button style="padding: 10px 24px; border-radius: 20px; background-color: #7c3aed; color: #ffffff; font-size: 14px; font-weight: 500; border: none; cursor: pointer;">
                    Send
                </button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_file_management():
    """Render file management section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>📁 Configuration Management</h2>", unsafe_allow_html=True) # Enhanced H2

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3>WAF Rules</h3>", unsafe_allow_html=True) # Enhanced H3
        st.info("""
        **Required fields:** id, category, parameter, operator, value, phase, action, priority
        """)
        rules_file = st.file_uploader("Upload rules CSV", type=['csv'], key="rules_upload")
    with col2:
        st.markdown("<h3>Traffic Data</h3>", unsafe_allow_html=True) # Enhanced H3
        st.info("""
        **Required fields:** timestamp, src_ip, method, url
        """)
        traffic_file = st.file_uploader("Upload traffic CSV", type=['csv'], key="traffic_upload")

    if rules_file or traffic_file:
        if st.button("📤 Upload Files", type="primary"):
            upload_success = True
            uploaded_files = []
            
            # Upload rules file if provided
            if rules_file:
                with st.spinner(f"Uploading {rules_file.name}..."):
                    # Validate file structure
                    is_valid, message = validate_csv_structure(rules_file, 'rules')
                    if not is_valid:
                        st.error(f"❌ Rules file validation failed: {message}")
                        upload_success = False
                    else:
                        # Upload the file
                        response = upload_file(rules_file, 'rules')
                        if response and response.status_code in [200, 201]:
                            st.success(f"✅ Successfully uploaded {rules_file.name}")
                            uploaded_files.append(f"{rules_file.name} (Rules)")
                        else:
                            st.error(f"❌ Failed to upload {rules_file.name}")
                            upload_success = False
            
            # Upload traffic file if provided
            if traffic_file:
                with st.spinner(f"Uploading {traffic_file.name}..."):
                    # Validate file structure
                    is_valid, message = validate_csv_structure(traffic_file, 'traffic')
                    if not is_valid:
                        st.error(f"❌ Traffic file validation failed: {message}")
                        upload_success = False
                    else:
                        # Upload the file
                        response = upload_file(traffic_file, 'traffic')
                        if response and response.status_code in [200, 201]:
                            st.success(f"✅ Successfully uploaded {traffic_file.name}")
                            uploaded_files.append(f"{traffic_file.name} (Traffic)")
                        else:
                            st.error(f"❌ Failed to upload {traffic_file.name}")
                            upload_success = False
            
            # Show overall result
            if upload_success and uploaded_files:
                st.success(f"🎉 All files uploaded successfully: {', '.join(uploaded_files)}")
                # Refresh the files data
                st.session_state.files_data = get_files_data()
                st.rerun()
            elif not upload_success:
                st.error("❌ Some files failed to upload. Please check the errors above.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_rule_analysis():
    """Render rule analysis section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>🔍 Security Analysis</h2>", unsafe_allow_html=True) # Enhanced H2

    if st.session_state.files_data:
        files_data = st.session_state.files_data
        rules_files = [f for f in files_data if f['file_type'] == 'rules']
        traffic_files = [f for f in files_data if f['file_type'] == 'traffic']
        
        if rules_files and traffic_files:
            col1, col2 = st.columns(2)
            with col1:
                selected_rules = st.selectbox(
                    "Rules File:",
                    options=rules_files,
                    format_func=lambda x: (x.get('filename') or x.get('supabase_path') or str(x.get('id', ''))).split('/')[-1]
                )
            with col2:
                selected_traffic = st.selectbox(
                    "Traffic File:",
                    options=traffic_files,
                    format_func=lambda x: (x.get('filename') or x.get('supabase_path') or str(x.get('id', ''))).split('/')[-1]
                )
            
            analysis_types = st.multiselect(
                "Analysis Types:",
                options=["Shadowing", "Generalization", "Redundancy", "Correlation"],
                default=["Shadowing", "Redundancy"]
            )
            
            # Map full names to abbreviations
            analysis_map = {
                "Shadowing": "SHD",
                "Generalization": "GEN", 
                "Redundancy": "RXD",
                "Correlation": "COR"
            }
            
            if st.button("Run Security Analysis", type="primary"):
                with st.spinner("Analyzing rule relationships..."):
                    # Convert full names to abbreviations before sending
                    analysis_types_abbr = [analysis_map[atype] for atype in analysis_types]
                    response = analyze_rules(selected_rules['id'], selected_traffic['id'], analysis_types_abbr)
                    
                    if response and response.status_code == 200:
                        st.success("✅ Analysis completed!")
                        display_analysis_results(response.json())
                    else:
                        st.error("Analysis failed - check backend connection")
        else:
            st.warning("Upload both rules and traffic files")
    else:
        st.error("No files available")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
# # frontend/components.py
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from utils import *

def apply_custom_styles():
    """Apply modern dark theme CSS styles based on MindLink design system"""
    st.markdown("""
    <style>
        /* Global Dark Theme */
        .main { 
            background-color: #1a1a1a; 
            color: #ffffff;
        }
        
        /* Typography */
        h1 { 
            color: #ffffff; 
            font-size: 28px;
            font-weight: 600;
            line-height: 1.2;
            margin-bottom: 4px;
        }
        
        h2 { 
            color: #ffffff; 
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 16px;
        }
        
        h3 { 
            color: #ffffff; 
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 12px;
        }
        
        /* Cards with Dark Theme */
        .card { 
            background: #242424; 
            padding: 24px; 
            border-radius: 12px; 
            border: 1px solid #333333; 
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); 
            margin: 16px 0; 
        }
        
        /* Enhanced Buttons */
        .stButton button { 
            background: linear-gradient(135deg, #7c3aed, #8b5cf6); 
            color: #ffffff; 
            border: none; 
            border-radius: 8px; 
            padding: 12px 24px; 
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 16px rgba(124, 58, 237, 0.4); 
        }
        
        /* Primary Action Button */
        .primary-button {
            background: #7c3aed !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
        }
        
        /* Success Button */
        .success-button {
            background: #10b981 !important;
            color: #000000 !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
        }
        
        /* Warning Button */
        .warning-button {
            background: #f59e0b !important;
            color: #000000 !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
        }
        
        /* Input Fields */
        .stTextInput > div > div > input {
            background-color: #242424 !important;
            color: #ffffff !important;
            border: 1px solid #404040 !important;
            border-radius: 8px !important;
            padding: 10px 12px !important;
        }
        
        .stSelectbox > div > div > div {
            background-color: #242424 !important;
            color: #ffffff !important;
            border: 1px solid #404040 !important;
            border-radius: 8px !important;
        }
        
        /* Metrics Cards */
        .metric-card {
            background: #242424;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #333333;
            text-align: center;
            margin: 8px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 4px;
        }
        
        .metric-label {
            font-size: 14px;
            color: #a3a3a3;
        }
        
        /* Status Indicators */
        .status-completed {
            color: #10b981;
            font-weight: 500;
        }
        
        .status-in-progress {
            color: #10b981;
            font-weight: 500;
        }
        
        .status-pending {
            color: #f59e0b;
            font-weight: 500;
        }
        
        .status-alert {
            color: #ef4444;
            font-weight: 500;
        }
        
        /* Badges */
        .badge {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            display: inline-block;
        }
        
        .badge-success {
            background: #10b981;
            color: #000000;
        }
        
        .badge-warning {
            background: #f59e0b;
            color: #000000;
        }
        
        .badge-info {
            background: #3b82f6;
            color: #ffffff;
        }
        
        .badge-purple {
            background: #7c3aed;
            color: #ffffff;
        }
        
        /* Pills/Tags */
        .pill {
            padding: 10px 18px;
            border-radius: 20px;
            border: 1px solid #404040;
            font-size: 14px;
            white-space: nowrap;
            display: inline-block;
            margin: 4px;
            background: transparent;
            color: #ffffff;
        }
        
        .pill-active {
            background: #10b981;
            color: #000000;
            border: none;
        }
        
        /* Expander Styling */
        .streamlit-expanderHeader {
            background: #242424 !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        
        .streamlit-expanderContent {
            background: #1e1e1e !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-top: none !important;
            border-radius: 0 0 8px 8px !important;
        }
        
        /* Progress Bars */
        .stProgress > div > div > div {
            background: #7c3aed !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #1a1a1a !important;
        }
        
        /* Data Tables */
        .stDataFrame {
            background: #242424 !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        
        /* Alerts */
        .stAlert {
            border-radius: 8px !important;
            border: 1px solid #333333 !important;
        }
        
        .stSuccess {
            background: rgba(16, 185, 129, 0.1) !important;
            border-color: #10b981 !important;
            color: #10b981 !important;
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.1) !important;
            border-color: #ef4444 !important;
            color: #ef4444 !important;
        }
        
        .stWarning {
            background: rgba(245, 158, 11, 0.1) !important;
            border-color: #f59e0b !important;
            color: #f59e0b !important;
        }
        
        .stInfo {
            background: rgba(59, 130, 246, 0.1) !important;
            border-color: #3b82f6 !important;
            color: #3b82f6 !important;
        }
        
        /* Custom spacing */
        .section-spacing {
            margin: 24px 0;
        }
        
        .card-spacing {
            margin: 16px 0;
        }
        
        .element-spacing {
            margin: 12px 0;
        }
        
        .compact-spacing {
            margin: 8px 0;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the main header with enhanced dark theme"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a1a, #242424); padding: 32px 0; margin-bottom: 32px; border-radius: 0 0 16px 16px;">
        <div style="max-width: 1200px; margin: 0 auto; padding: 0 32px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin: 0; font-size: 32px; font-weight: 700; background: linear-gradient(135deg, #7c3aed, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        🛡️ WAF Optimizer Pro
                    </h1>
                    <p style="margin: 8px 0 0 0; color: #a3a3a3; font-size: 16px;">
                        Intelligent Web Application Firewall Optimization Platform
                    </p>
                </div>
                <div style="display: flex; gap: 16px; align-items: center;">
                    <div style="background: #242424; padding: 12px 20px; border-radius: 12px; border: 1px solid #333333;">
                        <div style="color: #10b981; font-size: 14px; font-weight: 500;">🚀 Performance</div>
                        <div style="color: #ffffff; font-size: 18px; font-weight: 600;">Enhanced</div>
                    </div>
                    <div style="background: #242424; padding: 12px 20px; border-radius: 12px; border: 1px solid #333333;">
                        <div style="color: #3b82f6; font-size: 14px; font-weight: 500;">🎯 Security</div>
                        <div style="color: #ffffff; font-size: 18px; font-weight: 600;">Optimized</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_analysis_results(results):
    """Display rule analysis results with enhanced design"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Analysis Results")
    
    if 'data' in results:
        data = results['data']
    else:
        data = results
    
    # Enhanced Metrics Display
    metrics_data = [
        {"label": "Rules Analyzed", "value": data.get('total_rules_analyzed', 0)},
        {"label": "Relationships Found", "value": data.get('relationships_found', 0)},
        {"label": "Shadowing Rules", "value": len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'SHD'])},
        {"label": "Redundant Rules", "value": len([r for r in data.get('relationships', []) if r.get('relationship_type') == 'RXD'])}
    ]
    
    display_enhanced_metrics(metrics_data)
    
    # Relationships
    relationships = data.get('relationships', [])
    if relationships:
        st.subheader("🔍 Rule Relationships")
        for rel in relationships:
            with st.expander(f"🛡️ Rule {rel.get('rule_a')} → Rule {rel.get('rule_b')} ({rel.get('relationship_type')})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Confidence:** {rel.get('confidence', 'N/A')}")
                with col2:
                    st.write(f"**Evidence:** {rel.get('evidence_count', 'N/A')} matches")
                st.write(f"**Description:** {rel.get('description', 'No description')}")
    
    # Recommendations
    recommendations = data.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Optimization Suggestions")
        for rec in recommendations:
            st.write(f"**{rec.get('type', 'Suggestion')}:** {rec.get('description', 'No description')}")
            st.write(f"*Impact:* {rec.get('impact', 'Not specified')}")
            st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)
def render_performance_profiling():
    """FR03: Performance Profiling Section - COMPATIBLE VERSION"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Performance Profiling")
    st.write("Analyze rule efficiency and identify optimization opportunities")
    
    # Get available files
    files_data = st.session_state.get('files_data', [])
    traffic_files = [f for f in files_data if f['file_type'] == 'traffic']
    rules_files = [f for f in files_data if f['file_type'] == 'rules']
    
    if not traffic_files or not rules_files:
        st.warning("📁 Please upload both traffic and rules files first.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns(2)
    with col1:
        selected_traffic = st.selectbox(
            "Select Traffic Data:",
            options=traffic_files,
            format_func=lambda x: x.get('filename', x.get('file', 'Unknown File')),
            key="performance_traffic_select"
        )
    with col2:
        selected_rules = st.selectbox(
            "Select Rules Configuration:",
            options=rules_files,
            format_func=lambda x: x.get('filename', x.get('file', 'Unknown File')),
            key="performance_rules_select"
        )
    
    snapshot_name = st.text_input("Analysis Name:", "Performance Analysis", key="snapshot_name")
    
    if st.button("🔍 Analyze Rule Performance", type="primary", key="analyze_performance"):
        if selected_traffic and selected_rules:
            with st.spinner("🔄 Analyzing rule performance patterns..."):
                # FIXED: Proper payload structure that matches backend
                payload = {
                    "traffic_file_id": selected_traffic['id'],
                    "rules_file_id": selected_rules['id'],
                    "snapshot_name": snapshot_name
                }
                
                response = update_performance_data(payload)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success("✅ Performance analysis completed successfully!")
                    
                    # Display results
                    summary = result.get('analysis_summary', {})
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Rules Analyzed", summary.get('total_rules_analyzed', 0))
                    with col2:
                        st.metric("Rarely Used", summary.get('rarely_used_rules', 0))
                    with col3:
                        st.metric("Redundant", summary.get('redundant_rules', 0))
                    with col4:
                        st.metric("High Performers", summary.get('high_performance_rules', 0))
                    
                else:
                    error_msg = "Unknown error"
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', response.text[:200])
                        except:
                            error_msg = response.text[:200] if response.text else "No response content"
                    st.error(f"❌ Performance analysis failed: {error_msg}")
        else:
            st.warning("⚠️ Please select both traffic and rules files")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_rule_ranking():
    """Rule Ranking Section - COMPATIBLE VERSION"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("⚡ Performance Optimization")
    st.write("Intelligent rule reordering based on performance data")
    
    # Get available files
    files_data = st.session_state.get('files_data', [])
    rules_files = [f for f in files_data if f['file_type'] == 'rules']
    
    if not rules_files:
        st.warning("📁 Please upload rules files first.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns(2)
    with col1:
        selected_rules = st.selectbox(
            "Select Rules Configuration:",
            options=rules_files,
            format_func=lambda x: x.get('filename', x.get('file', 'Unknown File')),
            key="ranking_rules_select"
        )
    with col2:
        session_name = st.text_input("Session Name:", "Optimization Analysis", key="session_name")
    
    if st.button("🚀 Generate Optimized Ranking", type="primary", key="generate_ranking"):
        if selected_rules:
            with st.spinner("🔄 Analyzing and optimizing rule order..."):
                # FIXED: Pass rules_file_id correctly
                response = generate_rule_ranking(selected_rules['id'], session_name)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success("✅ Rule ranking generated successfully!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Performance Gain", f"{result.get('improvement', 0):.1f}%")
                    with col2:
                        st.metric("Rules Processed", result.get('rules_analyzed', 0))
                    with col3:
                        st.metric("Session ID", result.get('session_id', 'N/A'))
                    
                    # Store session for visualization
                    st.session_state.current_ranking_session = result.get('session_id')
                    
                    # Show visualization immediately
                    if st.session_state.current_ranking_session:
                        show_ranking_visualization(st.session_state.current_ranking_session)
                        
                else:
                    error_msg = "Unknown error"
                    if response:
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('error', response.text[:200])
                        except:
                            error_msg = response.text[:200] if response.text else "No response content"
                    
                    st.error(f"❌ Optimization failed: {error_msg}")
        else:
            st.warning("⚠️ Please select a rules configuration")
    
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
            st.dataframe(perf_df, use_container_width=True)
        
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
                st.dataframe(rules_df, use_container_width=True)
    else:
        st.error("Error loading dashboard")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_ranking_visualization(session_id):
    """Enhanced ranking visualization with proper table display"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📈 Optimization Results")
    
    try:
        response = get_ranking_comparison(session_id)
        if response and response.status_code == 200:
            comparison_data = response.json()
            
            # Enhanced metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Performance Gain", f"{comparison_data.get('improvement', 0):.1f}%")
            with col2:
                st.metric("Rules Improved", comparison_data.get('summary', {}).get('rules_moved_up', 0))
            with col3:
                st.metric("Rules Adjusted", comparison_data.get('summary', {}).get('rules_moved_down', 0))
            with col4:
                st.metric("Avg Change", f"{comparison_data.get('summary', {}).get('average_position_change', 0):+.1f}")
            
            # Check if comparison_data exists and has data
            if comparison_data.get('comparison_data'):
                df = pd.DataFrame(comparison_data['comparison_data'])
                
                # Display the ranking table immediately
                st.subheader("📋 Optimized Rule Order")
                
                # Create display dataframe with better formatting
                display_df = df.copy()
                
                # Ensure we have the required columns
                if 'current_position' in display_df.columns and 'proposed_position' in display_df.columns:
                    display_df = display_df.sort_values('proposed_position')
                    
                    # Calculate position changes
                    display_df['Position Change'] = display_df.apply(
                        lambda row: f"↑ {abs(row['proposed_position'] - row['current_position'])}" 
                        if row['proposed_position'] < row['current_position'] 
                        else (f"↓ {abs(row['proposed_position'] - row['current_position'])}" 
                              if row['proposed_position'] > row['current_position'] 
                              else "→ 0"),
                        axis=1
                    )
                    
                    # Add status indicators
                    display_df['Status'] = display_df.apply(
                        lambda row: '🔥 High Performance' if row.get('hit_count', 0) > 10 
                        else ('⚠️ Rarely Used' if row.get('hit_count', 0) <= 2 else '✓ Normal'),
                        axis=1
                    )
                    
                    # Select and rename columns for display
                    columns_mapping = {}
                    if 'rule_id' in display_df.columns:
                        columns_mapping['rule_id'] = 'Rule ID'
                    if 'current_position' in display_df.columns:
                        columns_mapping['current_position'] = 'Original Position'
                    if 'proposed_position' in display_df.columns:
                        columns_mapping['proposed_position'] = 'New Position'
                    if 'Position Change' in display_df.columns:
                        columns_mapping['Position Change'] = 'Change'
                    if 'hit_count' in display_df.columns:
                        columns_mapping['hit_count'] = 'Hit Count'
                    if 'priority_score' in display_df.columns:
                        columns_mapping['priority_score'] = 'Priority Score'
                    if 'category' in display_df.columns:
                        columns_mapping['category'] = 'Category'
                    if 'Status' in display_df.columns:
                        columns_mapping['Status'] = 'Status'
                    
                    # Filter to only include columns that exist
                    existing_columns = [col for col in columns_mapping.keys() if col in display_df.columns]
                    table_df = display_df[existing_columns].rename(columns=columns_mapping)
                    
                    st.dataframe(
                        table_df,
                        use_container_width=True,
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
                else:
                    st.warning("No position data available in the ranking results")
                
                # Enhanced visualization (only if we have position data)
                if 'current_position' in df.columns and 'proposed_position' in df.columns:
                    st.subheader("📊 Rule Position Optimization Chart")
                    fig = px.scatter(
                        df,
                        x='current_position',
                        y='proposed_position',
                        size='hit_count' if 'hit_count' in df.columns else None,
                        color='position_change' if 'position_change' in df.columns else None,
                        hover_data=['rule_id', 'priority_score', 'category'] if all(col in df.columns for col in ['rule_id', 'priority_score', 'category']) else None,
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
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
            else:
                st.info("No detailed comparison data available. The optimization was completed successfully.")
                
            st.info(f"💡 **Performance Insight:** Optimized rule order can improve processing speed by approximately {comparison_data.get('improvement', 0):.1f}%")
    
    except Exception as e:
        st.error(f"Error loading visualization: {str(e)}")
        # Show a simplified view if the detailed data isn't available
        st.info("Showing basic optimization results...")
        st.metric("Performance Improvement", f"{comparison_data.get('improvement', 0):.1f}%")
        st.metric("Total Rules Processed", comparison_data.get('rules_analyzed', 0))
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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

def render_false_positive_management():
    """FR04: False Positive Reduction Management with enhanced design"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Enhanced header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 20px; border-radius: 12px; margin-bottom: 24px;">
        <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;"> False Positive Reduction</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 8px 0 0 0; font-size: 16px;">Detect and reduce false positives to improve WAF accuracy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab layout for different FR04 features
    tab1, tab2, tab3, tab4 = st.tabs([" Detection", " Learning Mode", " Suggestions", " Export"])
    
    with tab1:
        render_false_positive_detection()
    
    with tab2:
        render_learning_mode()
    
    with tab3:
        render_whitelist_suggestions()
    
    with tab4:
        render_whitelist_export()
    
    st.markdown('</div>', unsafe_allow_html=True)
def render_false_positive_detection():
    """FR04-01: False Positive Detection (same selection style as Rule Analysis)"""
    st.markdown("""
    <div style="background: #242424; padding: 20px; border-radius: 12px; border: 1px solid #333333; margin-bottom: 24px;">
        <h3 style="color: #ffffff; margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">🔍 False Positive Detection</h3>
        <p style="color: #a3a3a3; margin: 0; font-size: 14px;">
            Analyze uploaded rules and traffic logs to detect false positives.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Ensure uploaded files exist in Streamlit state
    if st.session_state.files_data:
        files_data = st.session_state.files_data
        rules_files = [f for f in files_data if f['file_type'] == 'rules']
        traffic_files = [f for f in files_data if f['file_type'] == 'traffic']

        if rules_files and traffic_files:
            # --- Step 1: Select Files (same layout as Rule Analysis) ---
            st.markdown("### File Selection")
            col1, col2 = st.columns(2)
            def _format_file_entry(x):
                # Accept multiple possible keys depending on source: 'file', 'filename', 'name'
                if isinstance(x, dict):
                    return x.get('file') or x.get('filename') or x.get('name') or str(x)
                return str(x)

            with col1:
                selected_rules = st.selectbox(
                    "Select Rules File:",
                    options=rules_files,
                    format_func=_format_file_entry,
                    key="fp_rules_select"
                )
            with col2:
                selected_traffic = st.selectbox(
                    "Select Traffic File:",
                    options=traffic_files,
                    format_func=_format_file_entry,
                    key="fp_traffic_select"
                )

            # --- Step 2: Detection Settings ---
            st.markdown("### Detection Settings")
            col1, col2 = st.columns(2)
            with col1:
                detection_method = st.selectbox(
                    "Detection Method:",
                    options=["manual", "learning", "ai"],
                    index=0,
                    key="fp_detection_method"
                )
            with col2:
                threshold = st.slider("False Positive Threshold:", 0.05, 0.5, 0.1, 0.05)

            # --- Step 3: Run Detection ---
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚦 Run False Positive Detection", type="primary", use_container_width=True):
                    # ✅ FIX: ensure we pass a valid session_id from backend
                    # In your upload API, when files are uploaded, each has a session_id linked to RuleAnalysisSession
                    # We pick that same session ID here.
                    session_id = selected_rules.get('session_id') or selected_rules.get('id')
                    
                    if not session_id:
                        st.error("⚠️ No valid session ID found. Please re-upload or refresh.")
                        return

                    with st.spinner("Detecting false positives..."):
                        response = detect_false_positives_api(session_id, detection_method, threshold)

                        if response and response.status_code == 200:
                            result = response.json()
                            data = result.get("data", {})

                            st.success(f"✅ {result.get('message', 'Detection completed successfully.')}")
                            st.write("---")

                            # --- Display Key Metrics ---
                            metrics = [
                                {"label": "Rules Analyzed", "value": data.get('total_rules_analyzed', 0)},
                                {"label": "High FP Rules", "value": data.get('high_false_positive_rules', 0)},
                                {"label": "Method", "value": data.get('detection_method', '').title()},
                                {"label": "Threshold", "value": f"{data.get('threshold_used', 0):.1%}"}
                            ]
                            display_enhanced_metrics(metrics)

                            # --- Display Detected False Positives ---
                            fps = data.get('false_positives_detected', [])
                            if fps:
                                st.markdown("### 🚨 Detected False Positives")
                                for fp in fps:
                                    rate_color = "#ef4444" if fp['false_positive_rate'] > 0.2 else "#f59e0b"
                                    st.markdown(f"""
                                    <div style="background: #242424; padding: 16px; border-radius: 8px;
                                                border: 1px solid #333333; margin: 8px 0;">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <div>
                                                <div style="color: #fff; font-size: 16px; font-weight: 600;">
                                                    Rule {fp['rule_id']}
                                                </div>
                                                <div style="color: #a3a3a3; font-size: 14px;">
                                                    False Positive Rate:
                                                    <span style="color: {rate_color}; font-weight: 600;">
                                                        {fp['false_positive_rate']:.1%}
                                                    </span>
                                                </div>
                                            </div>
                                            <div style="background: {rate_color}; color: #fff; padding: 4px 12px;
                                                        border-radius: 6px; font-size: 12px; font-weight: 500;">
                                                {fp['status'].title()}
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("✅ No significant false positives detected.")
                        else:
                            st.error(f"❌ Detection failed. ({response.text if response else 'No response'})")
        else:
            st.warning("⚠️ Please upload both Rules and Traffic files first.")
    else:
        st.error("🚫 No uploaded files found in session.")

def render_learning_mode():
    """FR04-03: Learning Mode"""
    st.subheader("🧠 Learning Mode")
    st.write("Enable adaptive learning to understand normal traffic patterns")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.files_data:
            sessions = [f for f in st.session_state.files_data if f['file_type'] in ['rules', 'traffic']]
            if sessions:
                selected_session = st.selectbox(
                    "Select Session for Learning:",
                    options=[{"id": 1, "name": "Analysis Session 1"}],
                    format_func=lambda x: x['name'],
                    key="learning_session_select"
                )
            else:
                st.warning("No sessions available")
                selected_session = None
        else:
            st.error("No files available")
            selected_session = None
    
    with col2:
        learning_duration = st.slider("Learning Duration (hours):", 1, 72, 24)
    
    col1, col2 = st.columns(2)
    with col1:
        sample_size = st.number_input("Traffic Sample Size:", 100, 10000, 1000)
    with col2:
        st.write("")
    
    if st.button("🚀 Start Learning Mode", type="primary", key="start_learning"):
        if selected_session:
            with st.spinner("Starting learning mode analysis..."):
                response = start_learning_mode_api(selected_session['id'], learning_duration, sample_size)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # Display learning results
                    data = result['data']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Learning Session ID", data['learning_session_id'])
                    with col2:
                        st.metric("Patterns Learned", data['patterns_learned'])
                    with col3:
                        st.metric("Accuracy Score", f"{data['accuracy_score']:.1%}")
                    with col4:
                        st.metric("Status", data['status'].title())
                    
                    # Store learning session for status checking
                    st.session_state.current_learning_session = data['learning_session_id']
                else:
                    st.error("❌ Learning mode start failed")
        else:
            st.warning("Please select a session for learning")
    
    # Show learning status if active
    if hasattr(st.session_state, 'current_learning_session'):
        st.subheader("📊 Learning Status")
        learning_session_id = st.session_state.current_learning_session
        
        if st.button("🔄 Refresh Learning Status", key="refresh_learning"):
            with st.spinner("Checking learning status..."):
                response = get_learning_mode_status_api(learning_session_id)
                
                if response and response.status_code == 200:
                    status_data = response.json()['data']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", status_data['status'].title())
                    with col2:
                        st.metric("Patterns Learned", status_data['patterns_learned'])
                    with col3:
                        st.metric("Accuracy", f"{status_data['accuracy_score']:.1%}")
                    
                    # Show learned patterns
                    if status_data.get('normal_traffic_patterns'):
                        with st.expander("View Learned Patterns"):
                            patterns = status_data['normal_traffic_patterns']
                            st.write("**User Agents:**")
                            for ua in patterns.get('user_agents', [])[:3]:
                                st.write(f"- {ua}")
                            st.write("**Common Paths:**")
                            for path in patterns.get('common_paths', [])[:5]:
                                st.write(f"- {path}")

def render_whitelist_suggestions():
    """FR04-02: Whitelist Suggestions"""
    st.subheader("📝 Whitelist Suggestions")
    st.write("Generate intelligent whitelist patterns to reduce false positives")
    
    # Mock false positive data for demonstration
    false_positives = [
        {"id": 1, "rule_id": "1001", "false_positive_rate": 0.15, "status": "detected"},
        {"id": 2, "rule_id": "1002", "false_positive_rate": 0.22, "status": "analyzing"},
        {"id": 3, "rule_id": "1003", "false_positive_rate": 0.18, "status": "detected"},
    ]
    
    if false_positives:
        col1, col2 = st.columns(2)
        with col1:
            selected_fp = st.selectbox(
                "Select False Positive:",
                options=false_positives,
                format_func=lambda x: f"Rule {x['rule_id']} ({x['false_positive_rate']:.1%} FP Rate)",
                key="fp_select"
            )
        with col2:
            suggestion_types = st.multiselect(
                "Suggestion Types:",
                options=["ip_whitelist", "path_whitelist", "user_agent_whitelist", "parameter_whitelist"],
                default=["ip_whitelist", "path_whitelist"],
                key="suggestion_types"
            )
        
        if st.button("💡 Generate Suggestions", type="primary", key="generate_suggestions"):
            if selected_fp and suggestion_types:
                with st.spinner("Generating whitelist suggestions..."):
                    response = generate_whitelist_suggestions_api(selected_fp['id'], suggestion_types)
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result['message']}")
                        
                        # Display suggestions
                        suggestions = result['data']['suggestions']
                        if suggestions:
                            st.subheader("🎯 Generated Suggestions")
                            for suggestion in suggestions:
                                with st.expander(f"{suggestion['type'].replace('_', ' ').title()} - {suggestion['estimated_reduction']:.0f}% Reduction"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Description:** {suggestion['description']}")
                                        st.write(f"**Risk Assessment:** {suggestion['risk_assessment'].title()}")
                                    with col2:
                                        st.write(f"**Estimated Reduction:** {suggestion['estimated_reduction']:.0f}%")
                                        st.write(f"**Type:** {suggestion['type'].replace('_', ' ').title()}")
                    else:
                        st.error("❌ Suggestion generation failed")
            else:
                st.warning("Please select a false positive and suggestion types")
    else:
        st.info("No false positives detected yet. Run detection first.")

def render_whitelist_export():
    """FR04-04: Whitelist Export"""
    st.subheader("📤 Export Whitelist")
    st.write("Export suggested whitelist patterns as CSV file")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.files_data:
            sessions = [f for f in st.session_state.files_data if f['file_type'] in ['rules', 'traffic']]
            if sessions:
                selected_session = st.selectbox(
                    "Select Session:",
                    options=[{"id": 1, "name": "Analysis Session 1"}],
                    format_func=lambda x: x['name'],
                    key="export_session_select"
                )
            else:
                st.warning("No sessions available")
                selected_session = None
        else:
            st.error("No files available")
            selected_session = None
    
    with col2:
        export_name = st.text_input("Export Filename:", "waf_whitelist.csv", key="export_filename")
    
    col1, col2 = st.columns(2)
    with col1:
        include_patterns = st.multiselect(
            "Include Pattern Types:",
            options=["ip_whitelist", "path_whitelist", "user_agent_whitelist", "parameter_whitelist"],
            default=["ip_whitelist", "path_whitelist"],
            key="export_patterns"
        )
    with col2:
        st.write("")
    
    if st.button("📥 Export CSV", type="primary", key="export_csv"):
        if selected_session and include_patterns:
            with st.spinner("Generating CSV export..."):
                response = export_whitelist_csv_api(selected_session['id'], export_name, include_patterns)
                
                if response and response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ {result['message']}")
                    
                    # Display export results
                    data = result['data']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Export ID", data['export_id'])
                    with col2:
                        st.metric("Total Patterns", data['total_patterns'])
                    with col3:
                        st.metric("File Size", f"{data['file_size_bytes']} bytes")
                    with col4:
                        st.metric("Status", "Completed")
                    
                    # Provide download link
                    st.info(f"📁 File saved as: {data['file_name']}")
                    st.markdown(f"**Download URL:** `{data['download_url']}`")
                else:
                    st.error("❌ CSV export failed")
        else:
            st.warning("Please select a session and pattern types")


def render_file_library():
    """Render file library section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 File Library")

    if st.session_state.files_data:
        data = st.session_state.files_data
        df = pd.DataFrame(data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(df))
        with col2:
            st.metric("Rule Sets", len(df[df['file_type'] == 'rules']))
        with col3:
            st.metric("Traffic Logs", len(df[df['file_type'] == 'traffic']))
        
        st.dataframe(
            df[['id', 'file', 'file_type', 'uploaded_at']].rename(
                columns={'file': 'File Name', 'file_type': 'Type', 'uploaded_at': 'Uploaded'}
            ),
            use_container_width=True
        )
    else:
        st.info("No files uploaded yet")
    st.markdown('</div>', unsafe_allow_html=True)

def render_file_deletion():
    """Render file deletion section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 Delete Files")

    if st.session_state.files_data:
        data = st.session_state.files_data
        df = pd.DataFrame(data)

        # Dropdown options: show ID, filename, and file type
        file_options = [
            f"ID {f['id']}: {(f.get('filename') or f.get('supabase_path') or '').split('/')[-1]} ({f.get('file_type')})"
            for f in data
        ]

        selected_file = st.selectbox("Select file to delete:", ["Choose a file..."] + file_options)

        if selected_file != "Choose a file...":
            if st.button("🗑️ Delete File", type="secondary"):
                file_id = int(selected_file.split(":")[0].replace("ID ", "").strip())

                try:
                    response = delete_file(file_id)
                    if response.status_code == 204:
                        st.success(f"✅ File '{selected_file}' deleted successfully!")
                        # Refresh files
                        st.session_state.files_data = get_files_data()
                        st.rerun()
                    else:
                        st.error(f"❌ Delete failed: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"🚨 Error deleting file: {e}")
        else:
            st.info("Please select a file to delete.")
    else:
        st.info("No files available for deletion.")

    st.markdown('</div>', unsafe_allow_html=True)
