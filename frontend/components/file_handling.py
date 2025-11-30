import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *
from fetch_supabase_files import get_rules_files_from_supabase, get_traffic_files_from_supabase , download_file_from_supabase

def render_file_management():
    """Render file management section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2>📁 Configuration Management</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3>WAF Rules</h3>", unsafe_allow_html=True)
        st.info("""
        **Required fields:** id, category, parameter, operator, value, phase, action, priority
        """)
        rules_file = st.file_uploader("Upload rules CSV", type=['csv'], key="rules_upload")
    with col2:
        st.markdown("<h3>Traffic Data</h3>", unsafe_allow_html=True)
        st.info("""
        **Required fields:** timestamp, src_ip, method, url
        """)
        traffic_file = st.file_uploader("Upload traffic CSV", type=['csv'], key="traffic_upload")

    if rules_file or traffic_file:
        if st.button("📤 Upload Files", type="primary", width='stretch'):
            upload_success = True
            uploaded_files = []
            
            def is_duplicate_error(error_data):
                """Check if error indicates duplicate file"""
                if not error_data:
                    return False
                
                error_str = str(error_data)
                
                # Check direct string indicators
                if any(indicator in error_str for indicator in ['409', 'Duplicate', 'already exists']):
                    return True
                
                # Try to parse nested JSON error
                try:
                    # The error might be a string containing JSON
                    if error_str.startswith('{') and error_str.endswith('}'):
                        import json
                        parsed_error = json.loads(error_str.replace("'", '"'))
                        if parsed_error.get('statusCode') == 409:
                            return True
                        if 'duplicate' in str(parsed_error.get('message', '')).lower():
                            return True
                except:
                    pass
                
                return False
            
            # Upload rules file if provided
            if rules_file:
                with st.spinner(f"Uploading {rules_file.name}..."):
                    try:
                        # Validate file structure
                        is_valid, message = validate_csv_structure(rules_file, 'rules')
                        if not is_valid:
                            st.error(f"❌ Rules file validation failed: {message}")
                            upload_success = False
                        else:
                            # Upload the file
                            response = upload_file(rules_file, 'rules')
                            
                            # Handle response - check if it's a success response or error response
                            if response and isinstance(response, dict):
                                if response.get('id') or response.get('filename'):
                                    # Success case
                                    st.success(f"✅ Successfully uploaded {rules_file.name}")
                                    uploaded_files.append(f"{rules_file.name} (Rules)")
                                elif response.get('error'):
                                    # Error case returned from upload_file
                                    error_msg = response['error']
                                    status_code = response.get('status_code', 'Unknown')
                                    
                                    # Handle duplicate file error
                                    if is_duplicate_error(error_msg) or status_code == 409:
                                        st.warning(f"⚠️ File '{rules_file.name}' already exists. Please use a different filename or delete the existing file first.")
                                        upload_success = False
                                    else:
                                        st.error(f"❌ Failed to upload {rules_file.name} (Status {status_code}): {error_msg}")
                                        upload_success = False
                                else:
                                    st.error(f"❌ Unexpected response format for {rules_file.name}: {response}")
                                    upload_success = False
                            else:
                                st.error(f"❌ No valid response from server for {rules_file.name}")
                                upload_success = False
                    except Exception as e:
                        error_str = str(e)
                        if is_duplicate_error(error_str):
                            st.warning(f"⚠️ File '{rules_file.name}' already exists. Please use a different filename or delete the existing file first.")
                        else:
                            st.error(f"❌ Unexpected error uploading {rules_file.name}: {error_str}")
                        upload_success = False
            
            # Upload traffic file if provided
            if traffic_file:
                with st.spinner(f"Uploading {traffic_file.name}..."):
                    try:
                        # Validate file structure
                        is_valid, message = validate_csv_structure(traffic_file, 'traffic')
                        if not is_valid:
                            st.error(f"❌ Traffic file validation failed: {message}")
                            upload_success = False
                        else:
                            # Upload the file
                            response = upload_file(traffic_file, 'traffic')
                            
                            # Handle response - check if it's a success response or error response
                            if response and isinstance(response, dict):
                                if response.get('id') or response.get('filename'):
                                    # Success case
                                    st.success(f"✅ Successfully uploaded {traffic_file.name}")
                                    uploaded_files.append(f"{traffic_file.name} (Traffic)")
                                elif response.get('error'):
                                    # Error case returned from upload_file
                                    error_msg = response['error']
                                    status_code = response.get('status_code', 'Unknown')
                                    
                                    # Handle duplicate file error
                                    if is_duplicate_error(error_msg) or status_code == 409:
                                        st.warning(f"⚠️ File '{traffic_file.name}' already exists. Please use a different filename or delete the existing file first.")
                                        upload_success = False
                                    else:
                                        st.error(f"❌ Failed to upload {traffic_file.name} (Status {status_code}): {error_msg}")
                                        upload_success = False
                                else:
                                    st.error(f"❌ Unexpected response format for {traffic_file.name}: {response}")
                                    upload_success = False
                            else:
                                st.error(f"❌ No valid response from server for {traffic_file.name}")
                                upload_success = False
                    except Exception as e:
                        error_str = str(e)
                        if is_duplicate_error(error_str):
                            st.warning(f"⚠️ File '{traffic_file.name}' already exists. Please use a different filename or delete the existing file first.")
                        else:
                            st.error(f"❌ Unexpected error uploading {traffic_file.name}: {error_str}")
                        upload_success = False
            
            # Show overall result
            if upload_success and uploaded_files:
                st.success(f"🎉 All files uploaded successfully: {', '.join(uploaded_files)}")
                # Refresh the files data
                st.session_state.files_data = get_files_data()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_file_library():
    """Render file library section - fetches files directly from Supabase"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("📊 File Library")

    # Fetch files directly from Supabase buckets
    with st.spinner("Loading files from storage..."):
        rules_files = get_rules_files_from_supabase()
        logs_files = get_traffic_files_from_supabase()
    
    # Combine all files in the format expected by the original code
    all_files = []
    
    # Add rules files
    for file_info in rules_files:
        all_files.append({
            'id': f"rules_{file_info['name']}",  # Generate a unique ID
            'filename': file_info['name'],
            'file_type': 'rules',
            'file_size': file_info.get('size', 0),
            'uploaded_at': file_info.get('created_at', 'Unknown'),
            'bucket': file_info['bucket']
        })
    
    # Add logs files  
    for file_info in logs_files:
        all_files.append({
            'id': f"logs_{file_info['name']}",  # Generate a unique ID
            'filename': file_info['name'],
            'file_type': 'logs',
            'file_size': file_info.get('size', 0),
            'uploaded_at': file_info.get('created_at', 'Unknown'),
            'bucket': file_info['bucket']
        })
    
    if all_files:
        df = pd.DataFrame(all_files)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(df))
        with col2:
            st.metric("Rule Sets", len(df[df['file_type'] == 'rules']))
        with col3:
            st.metric("Logs Files", len(df[df['file_type'] == 'logs']))
        
        # Display the files table (same as original but with Supabase data)
        st.dataframe(
            df[['id', 'filename', 'file_type', 'uploaded_at']].rename(
                columns={'filename': 'File Name', 'file_type': 'Type', 'uploaded_at': 'Uploaded'}
            ),
            width='stretch'
        )
    else:
        st.info("No files found in Supabase storage")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_file_deletion():
    """Render file deletion section"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("🗑️ Delete Files")

    # Fetch files directly from Supabase buckets
    with st.spinner("Loading files from storage..."):
        rules_files = get_rules_files_from_supabase()
        logs_files = get_traffic_files_from_supabase()
    
    # Combine all files in the same format as before
    all_files = []
    
    # Add rules files
    for file_info in rules_files:
        all_files.append({
            'id': f"supabase_rules_{file_info['name']}",  # Generate ID for display
            'filename': file_info['name'],
            'file_type': 'rules',
            'display_name': f"{file_info['name']} (Rules)"
        })
    
    # Add logs files
    for file_info in logs_files:
        all_files.append({
            'id': f"supabase_logs_{file_info['name']}",  # Generate ID for display
            'filename': file_info['name'],
            'file_type': 'logs',
            'display_name': f"{file_info['name']} (Logs)"
        })

    if all_files:
        # FIX: Use 'filename' instead of 'file'
        file_options = [
            f"{f['display_name']}"
            for f in all_files
        ]

        selected_file = st.selectbox("Select file to delete:", ["Choose a file..."] + file_options)

        if selected_file != "Choose a file...":
            # Find the selected file details
            selected_file_info = next((f for f in all_files if f['display_name'] == selected_file), None)
            
            if st.button("🗑️ Delete File", type="secondary"):
                if selected_file_info:
                    try:
                        # Call modified delete_file function with filename and type
                        response = delete_file(selected_file_info['filename'], selected_file_info['file_type'])
                        
                        if response and response.status_code == 204:
                            st.success(f"✅ File '{selected_file}' deleted successfully!")
                            # Refresh files by rerunning
                            st.rerun()
                        else:
                            st.error(f"❌ Delete failed: {response.status_code if response else 'No response'} - {response.text if response else 'Unknown error'}")
                    except Exception as e:
                        st.error(f"🚨 Error deleting file: {e}")
        else:
            st.info("Please select a file to delete.")
    else:
        st.info("No files available for deletion.")

    st.markdown('</div>', unsafe_allow_html=True)


def render_file_selection(key_prefix: str = None):
    """
    Render file selection dropdowns for rules and logs files
    Fetches files directly from Supabase storage and stores in session state
    
    Returns:
        tuple: (selected_rules, selected_logs) or (None, None) if no files
    """
    # Display file selection header
    st.markdown("### 📁 File Selection")
    st.markdown("Select the rules and logs files for analysis:")
    # Prominent refresh control so users can repopulate lists without restarting
    rcol1, rcol2 = st.columns([1, 6])
    with rcol1:
        refresh_key = f"refresh_file_list_{key_prefix}" if key_prefix else "refresh_file_list"
        if st.button("🔄 Refresh file list", key=refresh_key):
            # Re-fetch and update session state
            rules_files = get_rules_files_from_supabase()
            logs_files = get_traffic_files_from_supabase()
            st.session_state.available_rules_files = rules_files
            st.session_state.available_logs_files = logs_files
            st.rerun()
    with rcol2:
        st.write("")
    
    # Initialize session state for file management
    if 'available_rules_files' not in st.session_state:
        st.session_state.available_rules_files = []
    if 'available_logs_files' not in st.session_state:
        st.session_state.available_logs_files = []
    if 'selected_rules_file' not in st.session_state:
        st.session_state.selected_rules_file = None
    if 'selected_logs_file' not in st.session_state:
        st.session_state.selected_logs_file = None
    if 'rules_file_content' not in st.session_state:
        st.session_state.rules_file_content = None
    if 'logs_file_content' not in st.session_state:
        st.session_state.logs_file_content = None
    
    # Fetch files directly from Supabase buckets
    with st.spinner("Loading files from storage..."):
        rules_files = get_rules_files_from_supabase()
        logs_files = get_traffic_files_from_supabase()
        
        # Store in session state for other modules to use
        st.session_state.available_rules_files = rules_files
        st.session_state.available_logs_files = logs_files
    
    # Debug info (optional)
    st.write(f"📊 Found {len(rules_files)} rules files, {len(logs_files)} logs files")
    
    if not rules_files or not logs_files:
        st.warning("⚠️ Please upload files to Supabase storage to proceed with analysis.")
        return None, None
    
    # Create file selection section with better visual separation
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**WAF Rules File**")
        key_rules = f"{key_prefix}_rules_file_selector" if key_prefix else "rules_file_selector"
        selected_rules = st.selectbox(
            "Select Rules File:", 
            options=rules_files, 
            format_func=lambda x: x['name'],
            key=key_rules,
            help="Choose the WAF rules file for analysis"
        )
        if selected_rules:
            st.info(f"Selected: {selected_rules['name']}")
    
    with col2:
        st.markdown("**Traffic Logs File**")
        key_logs = f"{key_prefix}_logs_file_selector" if key_prefix else "logs_file_selector"
        selected_logs = st.selectbox(
            "Select Logs File:", 
            options=logs_files, 
            format_func=lambda x: x['name'],
            key=key_logs,
            help="Choose the traffic logs file for analysis"
        )
        if selected_logs:
            st.info(f"Selected: {selected_logs['name']}")
    
    # Store selected files in session state
    if selected_rules:
        st.session_state.selected_rules_file = selected_rules
        # Pre-load content for other modules
        with st.spinner(f"Loading {selected_rules['name']}..."):
            st.session_state.rules_file_content = download_file_from_supabase(selected_rules['name'], 'rules')
    
    if selected_logs:
        st.session_state.selected_logs_file = selected_logs
        # Pre-load content for other modules
        with st.spinner(f"Loading {selected_logs['name']}..."):
            st.session_state.logs_file_content = download_file_from_supabase(selected_logs['name'], 'traffic')
    
    # Display success message if both files are loaded
    if selected_rules and selected_logs:
        st.success("✅ Files successfully loaded and ready for analysis!")
        st.markdown("---")
    
    return selected_rules, selected_logs

# Utility functions for other modules to access file data
def get_current_rules_file():
    """Get currently selected rules file from session state"""
    return st.session_state.get('selected_rules_file')

def get_current_logs_file():
    """Get currently selected logs file from session state"""
    return st.session_state.get('selected_logs_file')

def get_rules_file_content():
    """Get rules file content from session state"""
    return st.session_state.get('rules_file_content')

def get_logs_file_content():
    """Get logs file content from session state"""
    return st.session_state.get('logs_file_content')

def get_available_rules_files():
    """Get all available rules files from session state"""
    return st.session_state.get('available_rules_files', [])

def get_available_logs_files():
    """Get all available logs files from session state"""
    return st.session_state.get('available_logs_files', [])



