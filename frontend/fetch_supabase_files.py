# supabase_utils.py
import sys
import os
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase  # Import your Supabase client

def get_files_from_supabase_bucket(bucket_name):
    """Fetch files directly from Supabase storage bucket"""
    try:
        # Get list of files from Supabase bucket
        response = supabase.storage.from_(bucket_name).list()
        
        if response:
            files = []
            for file_info in response:
                files.append({
                    'name': file_info.get('name'),
                    'bucket': bucket_name,
                    'created_at': file_info.get('created_at'),
                    'updated_at': file_info.get('updated_at'),
                    'size': file_info.get('metadata', {}).get('size', 0)
                })
            return files
        else:
            return []
            
    except Exception as e:
        st.error(f"Error fetching files from {bucket_name}: {str(e)}")
        return []

def get_rules_files_from_supabase():
    """Get WAF rules files from Supabase bucket"""
    return get_files_from_supabase_bucket("waf-rule-files")

def get_traffic_files_from_supabase():
    """Get traffic files from Supabase bucket"""
    return get_files_from_supabase_bucket("waf-log-files")

def download_file_from_supabase(filename, file_type):
    """Download a specific file from Supabase storage"""
    try:
        # Determine the bucket based on file type
        bucket_name = "waf-rule-files" if file_type == 'rules' else "waf-log-files"
        
        # Download the file content
        file_content = supabase.storage.from_(bucket_name).download(filename)
        
        if file_content:
            return file_content
        else:
            st.error(f"Failed to download {filename} from {bucket_name}")
            return None
            
    except Exception as e:
        st.error(f"Error downloading {filename}: {str(e)}")
        return None