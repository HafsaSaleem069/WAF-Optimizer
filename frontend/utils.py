# frontend/utils.py
import requests
import streamlit as st

# API URLs
API_URL = "http://127.0.0.1:8000/api/files/"
FILES_SUMMARY_URL = "http://127.0.0.1:8000/api/files/summary/"
HEALTH_URL = "http://127.0.0.1:8000/api/health/"
RULE_ANALYSIS_API_URL = "http://127.0.0.1:8000/api/analyze/"
# Sessions endpoint (RuleAnalysisSession ViewSet registered as 'sessions')
SESSIONS_API_URL = "http://127.0.0.1:8000/api/sessions/"
RANKING_API_URL = "http://127.0.0.1:8000/api/ranking/generate/"
RANKING_COMPARISON_URL = "http://127.0.0.1:8000/api/ranking/comparison/"
HIT_COUNTS_UPDATE_URL = "http://127.0.0.1:8000/api/hit-counts/update/"
HIT_COUNTS_DASHBOARD_URL = "http://127.0.0.1:8000/api/hit-counts/dashboard/"
OPTIMIZATION_APPLY_URL = "http://127.0.0.1:8000/api/optimize/apply/"

def check_backend_status():
    """Check if backend is online"""
    try:
        response = requests.get(HEALTH_URL, timeout=3)
        return response.status_code == 200
    except:
        return False

def get_files_data():
    """Get uploaded files data"""
    try:
        response = requests.get(FILES_SUMMARY_URL)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and ('rules' in data or 'traffic' in data):
                rules = data.get('rules', []) or []
                traffic = data.get('traffic', []) or []
                return rules + traffic
            return data
        return []
    except:
        return []

def create_analysis_session(name, rules_file_id, traffic_file_id, analysis_types=None):
    """Create a RuleAnalysisSession via the backend API and return the session object"""
    try:
        if analysis_types is None:
            analysis_types = ['SHD', 'RXD', 'GEN', 'COR']
        data = {
            'name': name,
            'rules_file': rules_file_id,
            'traffic_file': traffic_file_id,
            'analysis_types': analysis_types
        }
        response = requests.post(SESSIONS_API_URL, json=data)
        return response
    except Exception as e:
        st.error(f"Create session error: {str(e)}")
        return None

def analyze_rules_by_session(session_id, analysis_types=None):
    """Request rule analysis for an existing backend session (session_id)."""
    try:
        data = {'session_id': session_id}
        if analysis_types:
            data['analysis_types'] = analysis_types
        response = requests.post(RULE_ANALYSIS_API_URL, json=data, timeout=60)
        return response
    except Exception as e:
        st.error(f"Analyze by session error: {str(e)}")
        return None

def analyze_rules(rules_content, logs_content, analysis_types):
    """Run rule analysis with file content as strings"""
    try:
        # Convert bytes to string if needed
        if isinstance(rules_content, bytes):
            rules_content = rules_content.decode('utf-8')
        if isinstance(logs_content, bytes):
            logs_content = logs_content.decode('utf-8')
        
        analysis_data = {
            'rules_content': rules_content,
            'logs_content': logs_content,
            'analysis_types': [atype[:3].upper() for atype in analysis_types]
        }
        
        response = requests.post(RULE_ANALYSIS_API_URL, json=analysis_data, timeout=60)
        return response
        
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def generate_rule_ranking(rules_file_id, session_name):
    """Generate optimized rule ranking"""
    # Prefer sending file content rather than ids
    try:
        import streamlit as st
        rules_content = None
        try:
            rules_content = st.session_state.get('rules_file_content')
        except Exception:
            pass

        # Decode bytes to string if necessary
        if isinstance(rules_content, (bytes, bytearray)):
            rules_content = rules_content.decode('utf-8')

        payload = {"session_name": session_name}
        if rules_content:
            payload['rules_content'] = rules_content
        else:
            # fallback to identifier if content missing
            payload['rules_file_id'] = rules_file_id

        response = requests.post(RANKING_API_URL, json=payload)
        return response
    except Exception as e:
        st.error(f"Ranking generation error: {str(e)}")
        return None

def get_ranking_comparison(session_id):
    """Get ranking comparison data"""
    try:
        response = requests.get(f"{RANKING_COMPARISON_URL}{session_id}/")
        return response
    except Exception as e:
        st.error(f"Ranking comparison error: {str(e)}")
        return None

def update_performance_data():
    """Update performance data (FR03)"""
    try:
        import streamlit as st
        # Send file contents instead of IDs
        rules_content = st.session_state.get('rules_file_content')
        logs_content = st.session_state.get('logs_file_content')

        # Decode bytes to string if necessary
        if isinstance(rules_content, (bytes, bytearray)):
            rules_content = rules_content.decode('utf-8')
        if isinstance(logs_content, (bytes, bytearray)):
            logs_content = logs_content.decode('utf-8')

        payload = {}
        if logs_content:
            payload['traffic_content'] = logs_content
        if rules_content:
            payload['rules_content'] = rules_content

        response = requests.post(HIT_COUNTS_UPDATE_URL, json=payload)
        return response
    except Exception as e:
        st.error(f"Performance update error: {str(e)}")
        return None

def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        response = requests.get(HIT_COUNTS_DASHBOARD_URL)
        return response
    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        return None

def upload_file(file, file_type):
    """Upload a file to the Django backend (which uploads to Supabase)"""
    try:
        files = {'file': (file.name, file, "text/csv")}
        data = {'file_type': file_type}
        response = requests.post(API_URL, files=files, data=data)
        
        if response.status_code in [200, 201]:
            return response.json()  # returns dict with 'filename', 'supabase_path', etc.
        else:
            # Return the error information so the calling function can handle it
            error_info = {
                'error': response.text,
                'status_code': response.status_code
            }
            return error_info
    except Exception as e:
        # Return the exception information so the calling function can handle it
        error_info = {
            'error': str(e),
            'status_code': 500
        }
        return error_info

def validate_csv_structure(file, file_type):
    """Validate CSV file structure based on file type"""
    try:
        import pandas as pd
        import io
        
        # Read the CSV file
        file.seek(0)  # Reset file pointer
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        file.seek(0)  # Reset file pointer again
        
        if file_type == 'rules':
            # Updated required fields for rules
            required_fields = [
                'rule_id', 'rule_name', 'rule_category', 'severity', 
                'pattern', 'action', 'description'
            ]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        elif file_type == 'traffic':
            # Updated required fields for traffic
            required_fields = [
                'timestamp', 'transaction_id', 'client_ip', 'http_status', 
                'request_method', 'request_uri', 'user_agent', 'rule_id', 
                'rule_message', 'matched_data', 'severity', 'attack_type', 
                'action', 'anomaly_score', 'phase'
            ]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, "File structure is valid"
        
    except Exception as e:
        return False, f"Error reading file: {str(e)}"
    
def delete_file(filename, file_type):
    
    """Delete a file by filename and type"""
    try:
        data = {
            'filename': filename,
            'file_type': file_type
        }
        response = requests.delete(f"{API_URL}delete_by_name", json=data)
        return response
    except Exception as e:
        st.error(f"Deletion error: {str(e)}")
        return None

# ===========================
# FR04: False Positive Detection Functions
# ===========================

# FR04: False Positive Reduction API URLs
FALSE_POSITIVE_ANALYZE_URL = "http://127.0.0.1:8000/api/analyzefalsepositive/"
WHITELIST_EXPORT_URL = "http://127.0.0.1:8000/api/export-whitelist/"


def analyze_false_positives_file_mode(rules_file_id, logs_file_id):
    """
    Analyze false positives using file upload mode
    
    Args:
        rules_file_id: ID of the rules file in the backend
        logs_file_id: ID of the logs/traffic file in the backend
    
    Returns:
        Response object from the API call
    """
    try:
        # This would need to be implemented based on your file handling
        # For now, we'll use a placeholder that indicates the mode
        data = {
            'mode': 'file_upload',
            'rules_file_id': rules_file_id,
            'logs_file_id': logs_file_id
        }
        
        # Note: The actual implementation depends on how your backend handles file uploads
        # You may need to send actual file objects using requests.post with files parameter
        
        response = requests.post(FALSE_POSITIVE_ANALYZE_URL, json=data, timeout=60)
        return response
    except Exception as e:
        st.error(f"File mode analysis error: {str(e)}")
        return None


def analyze_false_positives_session_mode(session_id):
    """
    Analyze false positives using existing session
    
    Args:
        session_id: ID of the RuleAnalysisSession
    
    Returns:
        Response object from the API call
    """
    try:
        data = {
            'session_id': session_id
        }
        
        response = requests.post(FALSE_POSITIVE_ANALYZE_URL, json=data, timeout=60)
        return response
    except Exception as e:
        st.error(f"Session mode analysis error: {str(e)}")
        return None


def analyze_false_positives_content_mode(rules_content, logs_content):
    """
    Analyze false positives using raw content strings
    
    Args:
        rules_content: CSV content of rules as string
        logs_content: CSV content of logs as string
    
    Returns:
        Response object from the API call
    """
    try:
        # Convert bytes to string if needed
        if isinstance(rules_content, bytes):
            rules_content = rules_content.decode('utf-8')
        if isinstance(logs_content, bytes):
            logs_content = logs_content.decode('utf-8')
        
        data = {
            'rules_content': rules_content,
            'logs_content': logs_content
        }
        
        response = requests.post(FALSE_POSITIVE_ANALYZE_URL, json=data, timeout=60)
        return response
    except Exception as e:
        st.error(f"Content mode analysis error: {str(e)}")
        return None


def get_false_positive_dashboard_api(session_id=None):
    """
    Get false positive dashboard data
    
    Args:
        session_id: Optional session ID to filter results
    
    Returns:
        Response object from the API call
    """
    try:
        params = {}
        if session_id:
            params['session_id'] = session_id
        
        response = requests.get(FALSE_POSITIVE_DASHBOARD_URL, params=params, timeout=30)
        return response
    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        return None


def export_whitelist_csv_api(session_id, export_name, include_patterns):
    """
    Export whitelist suggestions as CSV
    
    Args:
        session_id: ID of the analysis session
        export_name: Name for the exported CSV file
        include_patterns: List of pattern types to include (e.g., ['ip_whitelist', 'path_whitelist'])
    
    Returns:
        Response object from the API call
    """
    try:
        data = {
            'session_id': session_id,
            'export_name': export_name,
            'include_patterns': include_patterns
        }
        
        response = requests.post(WHITELIST_EXPORT_URL, json=data, timeout=30)
        return response
    except Exception as e:
        st.error(f"Whitelist export error: {str(e)}")
        return None


def get_file_content_by_id(file_id):
    """
    Fetch file content from backend by file ID
    
    Args:
        file_id: ID of the uploaded file
    
    Returns:
        File content as string or None if error
    """
    try:
        # Adjust this URL based on your actual file retrieval endpoint
        response = requests.get(f"http://127.0.0.1:8000/api/files/{file_id}/content/")
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        st.error(f"File content retrieval error: {str(e)}")
        return None


def validate_false_positive_session(session_id):
    """
    Validate that a session exists and is ready for false positive analysis
    
    Args:
        session_id: ID of the session to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if session exists in dashboard
        response = get_false_positive_dashboard_api(session_id)
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                return True, None
            else:
                return False, result.get('error', 'Unknown error')
        else:
            return False, 'Failed to validate session'
    except Exception as e:
        return False, str(e)

# In frontend/utils.py

def update_session_with_new_csv(new_csv_content):
    """
    Placeholder/helper: Updates the active file content in session state.
    (Assumes this function is defined elsewhere in utils.py)
    """
    # Assuming this function exists and works, or is where a potential error lies.
    st.session_state['rules_file_content'] = new_csv_content
    st.info("File content updated successfully in session state.")


# In frontend/utils.py

def apply_optimization_callback(button_key): 
    """
    Callback function executed when an 'Apply' button is clicked.
    Uses rules_content and filename (unique key) instead of a numeric ID,
    and ensures rules_content is correctly decoded to a string for JSON serialization.
    """
    try:
        print(f"\n--- CALLBACK STARTED ---")
        print(f"Key received: {button_key}")
        
        # 1. Retrieve essential data from session state
        relationship_data = st.session_state.get(f'data_{button_key}')
        
        if not relationship_data:
            error_msg = f"Error: Relationship data not found in session for key: {button_key}"
            print(f"❌ DEBUG EXIT 1: {error_msg}")
            st.session_state['status_message'] = error_msg
            return

        print(f"✅ Data retrieved successfully.")
        st.session_state['status_message'] = "Applying optimization via backend..."
        
        ai_suggestion = relationship_data.get('ai_suggestion', {})
        action = ai_suggestion.get('action')
        
        if not action:
            error_msg = "Error: No 'action' defined in AI suggestion."
            print(f"❌ DEBUG EXIT 2: {error_msg}")
            st.session_state['status_message'] = error_msg
            return
        
        # 2. Retrieve File Content & Name
        rules_content = st.session_state.get('rules_file_content')
        rules_file_name = st.session_state.get('selected_rules_file', {}).get('name')

        # 🌟 CRITICAL FIX: Decode content if it is a bytes object
        if isinstance(rules_content, bytes):
            try:
                # Decode bytes to string for JSON serialization
                rules_content = rules_content.decode('utf-8')
            except UnicodeDecodeError as e:
                error_msg = f"Error decoding file content: {e}"
                print(f"❌ DEBUG DECODE ERROR: {error_msg}")
                st.session_state['status_message'] = f"❌ File Decode Error: {error_msg}"
                return
        
        if not rules_content or not rules_file_name:
            error_msg = "Error: Rules file content or unique filename (Supabase key) not found in session."
            print(f"❌ DEBUG EXIT 3: {error_msg}")
            st.session_state['status_message'] = error_msg
            return

        # 3. Prepare payload for the backend
        payload = {
            "rules_file_name": rules_file_name,
            "rules_content": rules_content, # Now guaranteed to be a string
            "relationship_data": relationship_data,
            "action": action
        }

        print('✅ Payload prepared. Sending to backend...') 
        
        # 4. Send the instruction to the backend
        # Ensure OPTIMIZATION_APPLY_URL is accessible in this scope
        response = requests.post(
            OPTIMIZATION_APPLY_URL, 
            json=payload, 
            timeout=60
        )
        
        print(f"✅ Request sent. Status code received: {response.status_code}")
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'success':
            new_csv_content = result.get('new_csv_content')
            
            # 5. Process the backend response and update session state (Function assumed to exist)
            update_session_with_new_csv(new_csv_content)
            
            st.session_state['status_message'] = f"Successfully applied '{action}' optimization. File ready for export."
            print(f"✅ DEBUG SUCCESS: {st.session_state['status_message']}")
            st.experimental_rerun()
            
        else:
            error_msg = result.get('message', 'Unknown backend error.')
            print(f"❌ DEBUG BACKEND FAIL: {error_msg}")
            st.session_state['status_message'] = f"❌ Backend failed: {error_msg}"
            
    except requests.exceptions.RequestException as e:
        full_error = f"API Request failed: {e}"
        print(f"❌ DEBUG NETWORK ERROR: {full_error}")
        st.session_state['status_message'] = f"❌ Network Error: Could not reach backend to apply changes. See console for details."
        
    except Exception as e:
        full_error = f"Unexpected error in callback: {e}"
        print(f"❌ DEBUG UNEXPECTED ERROR: {full_error}")
        st.session_state['status_message'] = f"❌ Unexpected Callback Error: {full_error}"