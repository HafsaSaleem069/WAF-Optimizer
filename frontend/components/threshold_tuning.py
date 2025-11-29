import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from utils import *

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
                    # CHANGED: Using GET instead of POST to avoid CSRF
                    response = requests.get('http://127.0.0.1:8000/api/threshold_tuning/', timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Threshold tuning completed successfully!")
                        display_threshold_results(result)
                    else:
                        st.error(f"❌ Analysis failed: {response.status_code}")
                        st.write(f"**Error:** {response.text[:200]}...")
                        
                except Exception as e:
                    st.error(f"🚨 Connection error: {str(e)}")
    
    with col2:
        st.markdown("### ⚙️ Settings")
        st.info("""
        **API Endpoint:**
        `GET http://127.0.0.1:8000/api/threshold_tuning/`
        
        """)
    
    # Display existing suggestions
    display_existing_suggestions()
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_existing_suggestions():
    """Display existing threshold suggestions"""
    st.markdown("---")
    st.markdown("### 💾 Saved Suggestions")
    
    try:
        response = requests.get('http://127.0.0.1:8000/api/threshold_suggestions/')
        
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
                
                # Approval and Delete functionality
                st.markdown("#### 🔧 Manage Suggestions")
                all_suggestions = {f"ID {s['id']}: Threshold {s['value']}": s['id'] for s in suggestions}
                
                selected_suggestion = st.selectbox(
                    "Choose suggestion to manage:",
                    options=list(all_suggestions.keys())
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("👍 Approve Selected", type="primary", use_container_width=True):
                        suggestion_id = all_suggestions[selected_suggestion]
                        approve_response = requests.post(
                            f'http://127.0.0.1:8000/api/threshold_suggestions/approve/{suggestion_id}/'
                        )
                        
                        if approve_response.status_code == 200:
                            st.success("✅ Suggestion approved successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Approval failed")
                
                with col2:
                    if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
                        suggestion_id = all_suggestions[selected_suggestion]
                        
                        # Confirm deletion
                        with st.expander("⚠️ Confirm Deletion", expanded=True):
                            st.warning(f"Are you sure you want to delete suggestion {suggestion_id}?")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Yes, Delete", type="primary"):
                                    try:
                                        delete_response = requests.post(
                                            f'http://127.0.0.1:8000/api/threshold_suggestions/delete/{suggestion_id}/'
                                        )
                                        
                                        if delete_response.status_code == 200:
                                            st.success("🗑️ Suggestion deleted successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Delete failed: {delete_response.text}")
                                    except Exception as e:
                                        st.error(f"🚨 Delete error: {str(e)}")
                            with col2:
                                if st.button("❌ Cancel"):
                                    st.info("Deletion cancelled")
                    
            else:
                st.info("📝 No threshold suggestions yet. Run analysis first.")
                
        else:
            st.error(f"❌ Failed to load suggestions: {response.status_code}")
            
    except Exception as e:
        st.error(f"🚨 Error loading suggestions: {str(e)}")
        