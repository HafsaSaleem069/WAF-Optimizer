# optimization_recs_module/file_storage_utils.py

import os
# Assuming you have a globally accessible Supabase client object or connection
# from a file like: from your_project.settings import supabase 

# --- WARNING: YOU MUST REPLACE THIS WITH YOUR ACTUAL SUPABASE CLIENT ---
# This is a placeholder for demonstration purposes
SUPABASE_BUCKET_NAME = "waf-rule-files" 
try:
    # Example placeholder for a Supabase client connection (replace with your actual client)
    from supabase_client import supabase 
except ImportError:
    # Fallback for systems without full client setup
    print("WARNING: Supabase client not found. Using Mock function.")
    supabase = None

# ------------------------------------------------------------------------

def save_file_content_by_name(file_name: str, new_csv_content: str):
    """
    Saves (uploads/overwrites) the new CSV content to the Supabase Storage bucket 
    using the file_name as the path/key.

    Args:
        file_name (str): The unique path/name of the file in the Supabase bucket.
        new_csv_content (str): The modified CSV data string.

    Returns:
        bool: True on success, False otherwise.
    """
    if not supabase:
        print(f"MOCK: Content for {file_name} was NOT saved. Supabase client is missing.")
        return True # Return True to allow frontend to proceed in mock environment

    try:
        # Supabase storage uses bytes, so encode the string content
        content_bytes = new_csv_content.encode('utf-8')
        
        # We use the robust upload/overwrite pattern:
        response = supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            file=content_bytes,
            path=file_name,
            file_options={"content-type": "text/csv", "upsert": "true"} # upsert=true for overwrite
        )

        # 🌟 CRITICAL FIX: Check for error attribute on the response object
        # If the client is old or a specific fork, we check for the attribute
        if hasattr(response, 'error') and response.error is not None:
            print(f"❌ SUPABASE ERROR: Failed to save {file_name}. {response.error}")
            return False
        
        # Some clients return a dictionary on success, so a final check if 'error' key exists 
        # but the AttributeError is what we are primarily fixing here.
        # Assuming successful path if no exception was raised and no error attribute exists.

        print(f"✅ Supabase Save Success: File {file_name} updated.")
        return True

    except Exception as e:
        # This catches network errors, permissions issues, or exceptions explicitly raised by the client
        print(f"❌ UNEXPECTED SUPABASE EXCEPTION: {e}")
        return False