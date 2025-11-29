"""
Utility functions for fetching files from Supabase Storage
"""
import pandas as pd
import io
from supabase_client import supabase


def _value(uploaded_file, key):
    """Helper: get attribute or dict key from uploaded_file-like object"""
    if uploaded_file is None:
        return None
    if isinstance(uploaded_file, dict):
        return uploaded_file.get(key)
    return getattr(uploaded_file, key, None)


def get_file_from_supabase(uploaded_file):
    """
    Fetch file content from Supabase Storage based on UploadedFile model
    
    Args:
        uploaded_file: UploadedFile model instance
        
    Returns:
        bytes: File content from Supabase
    """
    supabase_path = _value(uploaded_file, 'supabase_path')
    filename = _value(uploaded_file, 'filename') or supabase_path
    file_type = _value(uploaded_file, 'file_type')

    if not uploaded_file or not supabase_path:
        raise ValueError(f"File {filename if filename else 'None'} has no Supabase path")

    # Determine bucket based on file type
    if file_type == 'rules':
        bucket_name = "waf-rule-files"
    elif file_type in ['traffic', 'logs']:
        bucket_name = "waf-log-files"
    else:
        raise ValueError(f"Unknown file type: {file_type}")
    
    try:
        # Download file from Supabase with a small retry on connection resets
        last_exc = None
        for attempt in range(2):
            try:
                file_content = supabase.storage.from_(bucket_name).download(supabase_path)
                return file_content
            except ConnectionResetError as cre:
                last_exc = cre
            except Exception as exc:
                # If it's not a connection reset, raise immediately
                raise
        # If we get here, we had connection resets
        raise Exception(f"Connection to Supabase storage aborted while downloading '{supabase_path}': {last_exc}")
    except Exception as e:
        # Raise the exception but include context so callers can attempt a fallback
        raise Exception(f"Failed to fetch file {filename} from Supabase: {str(e)}")


def get_file_as_dataframe(uploaded_file):
    """
    Fetch file from Supabase and convert to pandas DataFrame
    
    Args:
        uploaded_file: UploadedFile model instance
        
    Returns:
        pd.DataFrame: File content as DataFrame
    """
    try:
        file_content = get_file_from_supabase(uploaded_file)

        # Convert bytes to string if needed
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')

        # Read CSV from string
        df = pd.read_csv(io.StringIO(file_content))
        return df

    except Exception as e:
        # Supabase fetch failed — try local fallback using upload filename from the repo 'uploads' folder
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        fn = _value(uploaded_file, 'filename') or _value(uploaded_file, 'supabase_path')
        local_paths = [
            os.path.join(project_root, 'uploads', fn) if fn else None,
            os.path.join(project_root, 'uploads', 'uploads', fn) if fn else None,
            os.path.join(project_root, fn) if fn else None,
        ]

        for p in [p for p in local_paths if p]:
            try:
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as fh:
                        file_text = fh.read()
                    return pd.read_csv(io.StringIO(file_text))
            except Exception:
                continue

        # If fallback failed, re-raise the original exception (with context)
        raise Exception(f"Could not load file '{fn}' from Supabase or local fallbacks: {str(e)}")


def get_file_as_string(uploaded_file):
    """
    Fetch file from Supabase and return as string
    
    Args:
        uploaded_file: UploadedFile model instance
        
    Returns:
        str: File content as string
    """
    file_content = get_file_from_supabase(uploaded_file)
    
    # Convert bytes to string if needed
    if isinstance(file_content, bytes):
        return file_content.decode('utf-8')
    
    return file_content


def file_exists_in_supabase(uploaded_file):
    """
    Check if file exists in Supabase storage
    """
    try:
        file_type = _value(uploaded_file, 'file_type')
        if file_type == 'rules':
            bucket_name = "waf-rule-files"
        elif file_type in ['traffic', 'logs']:
            bucket_name = "waf-log-files"
        else:
            return False
        
        # Try to list the file
        files = supabase.storage.from_(bucket_name).list()
        path = _value(uploaded_file, 'supabase_path')
        return any(f['name'] == path for f in files)
    except:
        return False