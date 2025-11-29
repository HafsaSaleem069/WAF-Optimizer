from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from supabase_client import supabase
import io


def _query_first_existing_table(table_names):
    """Return (data, table_name) for the first table in table_names that exists.

    Tries each table name and returns the data and the table that worked.
    If none exist, returns (None, None).
    """
    for t in table_names:
        try:
            resp = supabase.table(t).select('*').execute()
            # try to extract data
            data = getattr(resp, 'data', None)
            if data is None:
                try:
                    json_body = resp.json() if hasattr(resp, 'json') else None
                    data = json_body.get('data') if json_body else None
                except Exception:
                    data = None

            # If response contains an explicit error message, skip this table
            if isinstance(data, dict) and data.get('error'):
                continue

            # If we got a list or non-empty result, return it
            if data is not None:
                return data, t

        except Exception:
            # ignore and try next table
            continue

    return None, None


@method_decorator(csrf_exempt, name='dispatch')
class UploadedFileViewSet(viewsets.ViewSet):
    """ViewSet that stores file bytes in Supabase Storage and file metadata in a
    Supabase table called `uploaded_files` using the Supabase REST API (service role key).

    This avoids relying on Django ORM for file metadata so the project can run
    using only Supabase credentials.
    """
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        try:
            files, used_table = _query_first_existing_table(['uploaded_files', 'files'])
            if files is None:
                return Response({'error': 'No metadata table found (tried uploaded_files, files)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Normalize records to ensure frontend-friendly keys
            normalized = []
            for f in files:
                try:
                    record = dict(f)
                except Exception:
                    record = f
                # Ensure keys exist
                record['id'] = record.get('id') or record.get('ID') or record.get('pk')
                # Some tables may use different column names
                record['filename'] = record.get('filename') or record.get('name') or record.get('file_name') or record.get('file')
                ft = record.get('file_type') or record.get('type') or record.get('filetype') or record.get('category')
                # Map legacy 'logs' to 'traffic' for frontend consistency
                if ft == 'logs':
                    ft = 'traffic'
                record['file_type'] = ft
                # keep table origin for debugging
                record['_meta_table'] = used_table
                normalized.append(record)

            return Response(normalized, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    @api_view(['GET'])
    def summary(request):
        """Return grouped files by type to simplify frontend consumption"""
        try:
            files, used_table = _query_first_existing_table(['uploaded_files', 'files'])
            if not files:
                return Response({'rules': [], 'traffic': [], 'table': None}, status=status.HTTP_200_OK)

            rules = []
            traffic = []
            for f in files:
                rec = dict(f) if not isinstance(f, dict) else f
                ft = rec.get('file_type') or rec.get('type') or rec.get('filetype') or rec.get('category')
                if ft == 'logs':
                    ft = 'traffic'
                # Normalize filename
                rec['filename'] = rec.get('filename') or rec.get('name') or rec.get('file_name') or rec.get('file')
                if ft == 'rules':
                    rules.append(rec)
                elif ft in ['traffic', 'logs']:
                    traffic.append(rec)

            return Response({'rules': rules, 'traffic': traffic, 'table': used_table}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'rules': [], 'traffic': [], 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        file_type = request.data.get('file_type')

        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if file_type == 'rules':
                bucket_name = 'waf-rule-files'
            elif file_type == 'traffic' or file_type == 'logs':
                bucket_name = 'waf-log-files'
            else:
                return Response({'error': "Invalid file type. Use 'rules' or 'traffic'"}, status=status.HTTP_400_BAD_REQUEST)

            # Upload to Supabase Storage
            file_content = file_obj.read()
            supabase.storage.from_(bucket_name).upload(file_obj.name, file_content)

            # Insert metadata into Supabase table
            record = {
                'filename': file_obj.name,
                'file_type': file_type,
                'file_size': file_obj.size,
                'supabase_path': file_obj.name
            }
            # Try inserting into the preferred table, fallback to 'files'
            for t in ['uploaded_files', 'files']:
                try:
                    insert_resp = supabase.table(t).insert(record).execute()
                    insert_data = getattr(insert_resp, 'data', None) or (insert_resp.json().get('data') if hasattr(insert_resp, 'json') else None)
                    # Return the inserted data if available
                    return Response(insert_data or {**record, '_meta_table': t}, status=status.HTTP_201_CREATED)
                except Exception:
                    # try next table
                    continue

            # If no metadata table exists, still return the record (storage was uploaded)
            return Response({**record, '_meta_table': None}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@csrf_exempt
def delete_file(request, file_id):
    """Delete a file from Supabase Storage and Supabase `uploaded_files` table by ID"""
    try:
        # Query the first existing table for this record
        files, used_table = _query_first_existing_table(['uploaded_files', 'files'])
        file_record = None
        if files:
            for r in files:
                rec = dict(r) if not isinstance(r, dict) else r
                rid = rec.get('id') or rec.get('ID') or rec.get('pk')
                if str(rid) == str(file_id):
                    file_record = rec
                    break

        if not file_record:
            return Response({'error': f'No file metadata found for id {file_id}'}, status=status.HTTP_404_NOT_FOUND)

        file_type = file_record.get('file_type') or file_record.get('type')
        supabase_path = file_record.get('supabase_path') or file_record.get('filename') or file_record.get('name')

        # Determine the correct bucket for deletion based on file type
        if file_type == 'rules':
            bucket_name = 'waf-rule-files'
        elif file_type == 'traffic' or file_type == 'logs':
            bucket_name = 'waf-log-files'
        else:
            bucket_name = 'waf-log-files'

        # Delete from storage
        supabase.storage.from_(bucket_name).remove([supabase_path])

        # Delete metadata record from Supabase table (try both tables)
        for t in ['uploaded_files', 'files']:
            try:
                supabase.table(t).delete().eq('id', file_id).execute()
            except Exception:
                continue

        return Response({'message': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@csrf_exempt
def delete_file_by_name(request):
    """Delete a file from Supabase Storage by filename (without database record)"""
    try:
        filename = request.data.get('filename')
        file_type = request.data.get('file_type')  # 'rules' or 'traffic'

        if not filename:
            return Response({"error": "filename is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not file_type:
            return Response({"error": "file_type is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine the correct bucket for deletion based on file type
        if file_type == 'rules':
            bucket_name = "waf-rule-files"
        elif file_type == 'traffic' or file_type == 'logs':  # Support both 'traffic' and 'logs' types
            bucket_name = "waf-log-files"  # Use consistent bucket name
        else:
            return Response({"error": f"Invalid file_type: {file_type}"}, status=status.HTTP_400_BAD_REQUEST)

        # Delete from the correct Supabase bucket
        result = supabase.storage.from_(bucket_name).remove([filename])
        
        # Check if deletion was successful
        if hasattr(result, 'error') and result.error:
            return Response({"error": f"Supabase deletion failed: {result.error.message}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Also try to delete metadata record from Supabase known tables
        db_message = ''
        for t in ['uploaded_files', 'files']:
            try:
                del_resp = supabase.table(t).delete().eq('filename', filename).eq('file_type', file_type).execute()
                deleted = getattr(del_resp, 'data', None) or (del_resp.json().get('data') if hasattr(del_resp, 'json') else None)
                if deleted:
                    db_message = ' and metadata record'
                    break
            except Exception:
                continue

        return Response({
            'message': f"File '{filename}' deleted successfully from {bucket_name}{db_message}"
        }, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """Simple health endpoint for frontend to verify backend is reachable"""
    try:
        return Response({'status': 'ok', 'message': 'Backend is up'}, status=200)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET'])
def files_raw(request):
    """Debug endpoint: return raw Supabase response for uploaded_files table."""
    try:
        data, used_table = _query_first_existing_table(['uploaded_files', 'files'])
        if data is None:
            return Response({'error': 'No metadata table found (tried uploaded_files, files)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'raw': data, 'table': used_table}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)