# false_positive/views.py - CORRECTED VERSION

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
import pandas as pd
import io
import traceback
import os
from datetime import datetime
from optimization_recs_module.models import RuleAnalysisSession
from .models import FalsePositiveDetection, WhitelistSuggestion
from .serializers import FalsePositiveDetectionSerializer, WhitelistSuggestionSerializer

# -------------------------------
# 1️⃣ Analyze False Positives (CORRECTED)
# -------------------------------
@api_view(['POST'])
def analyze_false_positives(request):
    try:
        rules_content, logs_content = None, None
        session_id = request.data.get('session_id')

        if session_id:
            return Response({'error': 'Session loading not implemented'},
                            status=status.HTTP_501_NOT_IMPLEMENTED)

        elif request.FILES:
            rules_file = request.FILES.get('rules_file')
            logs_file = request.FILES.get('logs_file')

            if not rules_file or not logs_file:
                return Response({'error': 'Both files are required'}, status=400)

            rules_content = rules_file.read().decode('utf-8')
            logs_content = logs_file.read().decode('utf-8')

        elif request.data.get('rules_content') and request.data.get('logs_content'):
            rules_content = request.data.get('rules_content')
            logs_content = request.data.get('logs_content')

        else:
            return Response({'error': 'No data provided'}, status=400)

        # ========================================
        # STEP 1: Parse CSV files
        # ========================================
        try:
            print("\n" + "="*60)
            print("PARSING CSV FILES")
            print("="*60)
            
            rules_df = pd.read_csv(
                io.StringIO(rules_content),
                skipinitialspace=True,
                on_bad_lines='warn'
            )
            
            logs_df = pd.read_csv(
                io.StringIO(logs_content),
                skipinitialspace=True,
                on_bad_lines='warn'
            )
            
            print(f"✓ Rules loaded: {rules_df.shape[0]} rows, {rules_df.shape[1]} columns")
            print(f"  Columns: {list(rules_df.columns)}")
            print(f"\n✓ Logs loaded: {logs_df.shape[0]} rows, {logs_df.shape[1]} columns")
            print(f"  Columns: {list(logs_df.columns)}")
            
        except Exception as e:
            print(f"✗ CSV Parsing Error: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'error': f'CSV parsing failed: {str(e)}',
                'hint': 'Check if files are properly formatted CSV'
            }, status=400)

        # ========================================
        # STEP 2: Validate data loaded correctly
        # ========================================
        if rules_df.empty:
            return Response({
                'error': 'Rules file is empty after parsing',
                'columns_found': list(rules_df.columns)
            }, status=400)
            
        if logs_df.empty:
            return Response({
                'error': 'Logs file is empty after parsing',
                'columns_found': list(logs_df.columns)
            }, status=400)

        # ========================================
        # STEP 3: Check required columns
        # ========================================
        print(f"\n" + "="*60)
        print("VALIDATING COLUMNS")
        print("="*60)
        
        required_log_cols = ["rule_id", "action"]
        missing_log_cols = [c for c in required_log_cols if c not in logs_df.columns]
        
        if missing_log_cols:
            return Response({
                "error": "Logs file missing required columns",
                "missing_columns": missing_log_cols,
                "provided_columns": list(logs_df.columns),
                "hint": "Required: rule_id, action"
            }, status=400)
        
        if 'rule_id' not in rules_df.columns:
            return Response({
                "error": "Rules file missing 'rule_id' column",
                "provided_columns": list(rules_df.columns)
            }, status=400)
        
        print(f"✓ All required columns present")

        # ========================================
        # FIX: Add missing columns with defaults
        # ========================================
        if 'matched_data' not in logs_df.columns:
            logs_df['matched_data'] = ""
            print("⚠ Added missing 'matched_data' column with empty values")
        
        if 'request_uri' not in logs_df.columns:
            logs_df['request_uri'] = ""
            print("⚠ Added missing 'request_uri' column with empty values")
        
        if 'severity' not in logs_df.columns:
            logs_df['severity'] = "medium"
            print("⚠ Added missing 'severity' column with default 'medium'")

        # ========================================
        # STEP 4: Clean and prepare data
        # ========================================
        print(f"\n" + "="*60)
        print("PREPARING DATA")
        print("="*60)
        
        # Convert rule_id to string and strip whitespace
        logs_df['rule_id'] = logs_df['rule_id'].astype(str).str.strip()
        rules_df['rule_id'] = rules_df['rule_id'].astype(str).str.strip()
        
        # FIX: Handle mixed case actions (BLOCKED, Blocked, BLOCK, etc.)
        logs_df['action'] = logs_df['action'].astype(str).str.strip().str.lower()
        # Normalize variations
        logs_df['action'] = logs_df['action'].replace({
            'block': 'blocked',
            'deny': 'blocked',
            'reject': 'blocked'
        })
        
        # Filter blocked and allowed requests
        blocked_logs = logs_df[logs_df['action'] == 'blocked'].copy()
        allowed_logs = logs_df[logs_df['action'].isin(['allowed', 'allow', 'pass'])].copy()
        
        print(f"Total logs: {len(logs_df)}")
        print(f"Blocked logs: {len(blocked_logs)}")
        print(f"Allowed logs: {len(allowed_logs)}")
        print(f"\nUnique actions in logs: {logs_df['action'].unique()}")
        print(f"Unique rule_ids in logs: {sorted(logs_df['rule_id'].unique())}")
        print(f"Unique rule_ids in rules: {sorted(rules_df['rule_id'].unique())}")

        # ========================================
        # STEP 5: Check if we have any data to analyze
        # ========================================
        if len(blocked_logs) == 0:
            print("\n⚠ WARNING: No blocked requests found!")
            return Response({
                "status": "success",
                "session_id": None,
                "total_logs_analyzed": len(logs_df),
                "total_blocked": 0,
                "false_positives_detected": 0,
                "false_positives": [],
                "whitelist_suggestions": [],
                "message": "No blocked requests found. All traffic was allowed.",
                "debug": {
                    "unique_actions": logs_df['action'].unique().tolist(),
                    "action_counts": logs_df['action'].value_counts().to_dict(),
                    "sample_logs": logs_df.head(5).to_dict('records')
                }
            }, status=200)

        # ========================================
        # STEP 6: Create session
        # ========================================
        session = RuleAnalysisSession.objects.create(
            name=f"FP Session {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            analysis_types=["FPD"]
        )
        print(f"\n✓ Created session: {session.id}")

        results = []
        whitelist_suggestions = []

        # ========================================
        # STEP 7: Analyze each rule
        # ========================================
        print(f"\n" + "="*60)
        print("ANALYZING RULES FOR FALSE POSITIVES")
        print("="*60)
        
        for idx, rule in rules_df.iterrows():
            rule_id = str(rule['rule_id']).strip()
            
            if pd.isna(rule_id) or rule_id == '' or rule_id == 'nan':
                continue
            
            # Get blocked and allowed logs for this rule
            rule_blocked_logs = blocked_logs[blocked_logs['rule_id'] == rule_id].copy()
            rule_allowed_logs = allowed_logs[allowed_logs['rule_id'] == rule_id].copy()
            
            if len(rule_blocked_logs) == 0:
                continue
            
            print(f"\n→ Analyzing Rule: {rule_id}")
            print(f"  Total blocks: {len(rule_blocked_logs)}")
            print(f"  Total allowed: {len(rule_allowed_logs)}")

            # ========================================
            # STEP 8: CORRECTED False Positive Detection
            # ========================================
            def is_likely_false_positive(log_row):
                """
                CORRECTED HEURISTIC - More strict detection
                Only marks as FP if truly benign patterns
                """
                matched_data = str(log_row.get('matched_data', '')).lower().strip()
                request_uri = str(log_row.get('request_uri', '')).lower().strip()
                severity = str(log_row.get('severity', '')).lower().strip()
                
                # Skip if no data to analyze
                if not matched_data and not request_uri:
                    return False
                
                # FIX: Use EXACT matching for SQL keywords - not substring
                # Only mark as FP if it's a standalone sorting parameter
                sql_keywords = ['desc', 'asc', 'select', 'order', 'from', 'where']
                is_standalone_sql_keyword = (
                    matched_data in sql_keywords and 
                    len(matched_data) == len(matched_data.strip()) and
                    any(param in request_uri for param in ["sort=", "order=", "direction=", "filter="])
                )
                
                # False positive patterns (corrected)
                fp_indicators = [
                    # Legitimate brand names with special chars (exact match)
                    matched_data in ["o'reilly", "o'clock", "it's", "don't", "won't", "at&t", "barnes&noble", "h&m"],
                    
                    # Legitimate documentation paths
                    ("javascript" in request_uri or "script" in request_uri) and
                    any(path in request_uri for path in ["/documentation/", "/docs/", "/learn/", "/tutorial/", "/examples/"]),
                    
                    # Analytics/tracking legitimate event handlers
                    matched_data in ["onclick", "onerror", "onload"] and
                    any(path in request_uri for path in ["/analytics/", "/tracking/", "/metrics/", "/tag-manager/"]),
                    
                    # SQL keywords ONLY as sorting params (standalone exact match)
                    is_standalone_sql_keyword,
                    
                    # Numeric category IDs
                    "category=" in request_uri and matched_data.isdigit() and len(matched_data) <= 4,
                    
                    # HTML entities (exact match)
                    matched_data in ["<3", "&lt;", "&gt;", "&amp;", "&nbsp;"],
                    
                    # Low severity + very short matches (likely false alarms)
                    severity in ["low"] and len(matched_data) <= 3,
                    
                    # Static file extensions in legitimate paths
                    matched_data in [".js", ".css", ".png", ".jpg", ".gif", ".svg", ".woff", ".ttf"] and
                    any(path in request_uri for path in ["/assets/", "/static/", "/public/", "/dist/", "/cdn/"]),
                    
                    # Known safe parameter patterns
                    "utm_" in request_uri and matched_data in ["source", "medium", "campaign"],
                ]
                
                return any(fp_indicators)
            
            # Apply detection
            rule_blocked_logs['is_false_positive'] = rule_blocked_logs.apply(
                is_likely_false_positive, axis=1
            )
            
            false_positives = rule_blocked_logs[rule_blocked_logs['is_false_positive']]
            fp_count = len(false_positives)
            
            print(f"  False positives: {fp_count}")
            
            if fp_count == 0:
                print(f"  ✓ No false positives detected")
                continue
            
            # FIX: Calculate correct metrics
            total_blocked = len(rule_blocked_logs)
            legitimate_request_count = len(rule_allowed_logs)  # FIXED: Actual allowed requests
            fp_rate = fp_count / total_blocked if total_blocked > 0 else 0
            
            print(f"  ✓ FP Rate: {fp_rate:.1%}")
            print(f"  ✓ Legitimate allowed: {legitimate_request_count}")
            
            # Show sample FPs
            if fp_count > 0:
                print(f"  Sample false positives:")
                for i, (_, fp) in enumerate(false_positives.head(3).iterrows()):
                    print(f"    {i+1}. URI: {fp.get('request_uri', 'N/A')[:50]}")
                    print(f"       Matched: '{fp.get('matched_data', 'N/A')}'")

            # ========================================
            # STEP 9: Create detection record (CORRECTED)
            # ========================================
            fp_obj, created = FalsePositiveDetection.objects.update_or_create(
                session=session,
                rule_id=rule_id,
                defaults={
                    "false_positive_count": fp_count,
                    "legitimate_request_count": legitimate_request_count,  # FIXED
                    "false_positive_rate": fp_rate,
                    "blocked_requests": false_positives.to_dict(orient="records"),
                    "request_patterns": {
                        'common_uris': false_positives['request_uri'].value_counts().head(5).to_dict()
                                    if 'request_uri' in false_positives.columns else {},
                        'common_matched_data': false_positives['matched_data'].value_counts().head(5).to_dict()
                                    if 'matched_data' in false_positives.columns else {}
                    },
                    "detection_method": "corrected_heuristic",
                    "confidence_score": 0.85,
                }
            )

            # ========================================
            # STEP 10: Generate whitelist suggestions (CORRECTED)
            # ========================================
            if 'request_uri' in false_positives.columns and len(false_positives) > 0:
                path_counts = false_positives['request_uri'].value_counts()
                
                # Track generated patterns to avoid duplicates
                generated_patterns = set()
                
                for path_value, count in path_counts.head(5).items():  # Top 5 instead of 3
                    if pd.isna(path_value) or str(path_value).strip() == '':
                        continue
                    
                    # FIX: Better path cleaning (remove query params AND fragments)
                    base_path = str(path_value).split('?', 1)[0].split('#', 1)[0]
                    
                    # FIX: Skip static file paths unless very common
                    is_static = any(static in base_path for static in ['/static/', '/assets/', '/cdn/'])
                    if is_static and count < 5:
                        continue
                    
                    # Avoid duplicates
                    if base_path in generated_patterns:
                        continue
                    
                    generated_patterns.add(base_path)
                    
                    # FIX: Correct reduction calculation
                    estimated_reduction = count / fp_count if fp_count > 0 else 0  # FIXED
                    
                    # Better risk assessment
                    if count >= 10:
                        risk = "low"
                    elif count >= 5:
                        risk = "medium"
                    else:
                        risk = "high"
                    
                    # Better priority
                    if fp_rate > 0.5 and count >= 5:
                        priority = "high"
                    elif fp_rate > 0.3:
                        priority = "medium"
                    else:
                        priority = "low"
                    
                    ws_obj = WhitelistSuggestion.objects.create(
                        false_positive=fp_obj,
                        suggestion_type="path_whitelist",
                        pattern_description=f"Allow path: {base_path} ({count} occurrences, {estimated_reduction:.1%} reduction)",
                        pattern_conditions={"path": base_path, "occurrences": count},
                        estimated_false_positive_reduction=estimated_reduction,
                        security_risk_assessment=risk,
                        implementation_priority=priority
                    )
                    
                    whitelist_suggestions.append(
                        WhitelistSuggestionSerializer(ws_obj).data
                    )

            results.append(FalsePositiveDetectionSerializer(fp_obj).data)

        # ========================================
        # STEP 11: Return results
        # ========================================
        print(f"\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total false positives detected: {len(results)}")
        print(f"Whitelist suggestions generated: {len(whitelist_suggestions)}")
        print("="*60 + "\n")

        return Response({
            "status": "success",
            "session_id": session.id,
            "total_logs_analyzed": len(logs_df),
            "total_blocked": len(blocked_logs),
            "total_allowed": len(allowed_logs),
            "false_positives_detected": len(results),
            "false_positives": results,
            "whitelist_suggestions": whitelist_suggestions,
            "debug": {
                "rules_in_file": len(rules_df),
                "rules_with_blocks": len(blocked_logs['rule_id'].unique()),
                "unique_rule_ids_in_logs": sorted(logs_df['rule_id'].unique().tolist()),
                "unique_rule_ids_in_rules": sorted(rules_df['rule_id'].unique().tolist()),
                "blocked_by_rule": blocked_logs.groupby('rule_id').size().to_dict()
            }
        }, status=200)

    except Exception as e:
        print("\n" + "="*60)
        print("EXCEPTION OCCURRED")
        print("="*60)
        print(traceback.format_exc())
        print("="*60 + "\n")
        return Response({
            'error': str(e), 
            'traceback': traceback.format_exc()
        }, status=500)


# -------------------------------
# 3️⃣ Export Whitelist CSV (Already correct)
# -------------------------------
@api_view(['POST'])
def export_whitelist_csv(request):
    try:
        session_id = request.data.get('session_id')
        export_name = request.data.get('export_name', f'waf_whitelist_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        include_patterns = request.data.get('include_patterns', ['path_whitelist'])

        print(f"\n{'='*60}")
        print(f"WHITELIST EXPORT REQUEST")
        print(f"{'='*60}")
        print(f"Session ID (provided): {session_id}")
        print(f"Export name: {export_name}")
        print(f"Include patterns: {include_patterns}")

        if not session_id:
            print(f"\n⚠ No session_id provided - using latest session")
            latest_session = RuleAnalysisSession.objects.filter(
                analysis_types__contains='FPD'
            ).order_by('-created_at').first()
            
            if not latest_session:
                print(f"✗ No false positive analysis session found")
                return Response({
                    'error': 'No analysis session found. Please run a false positive analysis first.',
                    'hint': 'Go to "Detection & Analysis" tab and click "Run Analysis"'
                }, status=404)
            
            session = latest_session
            print(f"✓ Using latest session: {session.id} - {session.name}")
        else:
            try:
                session = get_object_or_404(RuleAnalysisSession, id=session_id)
                print(f"✓ Session found: {session.name}")
            except Exception as e:
                print(f"✗ Session not found: {str(e)}")
                return Response({'error': f'Session {session_id} not found'}, status=404)

        suggestions = WhitelistSuggestion.objects.filter(
            false_positive__session=session,
            suggestion_type__in=include_patterns,
            status__in=['suggested', 'approved']
        )

        total_suggestions = suggestions.count()
        print(f"\nQuery results:")
        print(f"  Total suggestions found: {total_suggestions}")
        
        breakdown = {}
        for pattern_type in include_patterns:
            count = suggestions.filter(suggestion_type=pattern_type).count()
            breakdown[pattern_type] = count
            print(f"  - {pattern_type}: {count}")

        if total_suggestions == 0:
            print(f"\n⚠ WARNING: No suggestions found!")
            all_suggestions = WhitelistSuggestion.objects.filter(false_positive__session=session)
            all_count = all_suggestions.count()
            print(f"  Total suggestions (any type): {all_count}")
            
            if all_count > 0:
                available_types = list(all_suggestions.values_list('suggestion_type', flat=True).distinct())
                return Response({
                    'status': 'error',
                    'error': 'No whitelist suggestions match the selected pattern types',
                    'available_types': available_types,
                    'requested_types': include_patterns,
                    'hint': f'This session has {all_count} suggestions, but none match your selection.'
                }, status=400)
            else:
                fps = FalsePositiveDetection.objects.filter(session=session)
                fp_count = fps.count()
                
                if fp_count == 0:
                    return Response({
                        'status': 'error',
                        'error': 'No false positives detected in this session',
                        'hint': 'The analysis found no false positives.'
                    }, status=400)

        rows = []
        for s in suggestions:
            rows.append({
                'rule_id': s.false_positive.rule_id,
                'suggestion_type': s.suggestion_type,
                'pattern_description': s.pattern_description,
                'pattern_regex': s.pattern_regex or '',
                'pattern_conditions': str(s.pattern_conditions),
                'estimated_reduction': f"{s.estimated_false_positive_reduction:.2%}",
                'security_risk': s.security_risk_assessment,
                'priority': s.implementation_priority,
                'status': s.status,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        df = pd.DataFrame(rows)
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, export_name)
        df.to_csv(file_path, index=False)

        print(f"\n✓ Export successful!")
        print(f"  File path: {file_path}")
        print(f"  Total patterns: {len(rows)}")
        print(f"{'='*60}\n")

        return Response({
            'status': 'success',
            'file_path': file_path,
            'file_name': export_name,
            'total_patterns': len(rows),
            'breakdown': breakdown,
            'session_id': session.id,
            'session_name': session.name
        }, status=200)

    except Exception as e:
        print(f"\n✗ Export error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'status': 'error',
            'error': str(e), 
            'traceback': traceback.format_exc()
        }, status=500)