from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ThresholdSuggestion
import pandas as pd
import numpy as np
import os
from supabase import create_client
from dotenv import load_dotenv
from io import StringIO

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


@api_view(['POST'])
def delete_threshold_suggestion(request, suggestion_id):
    """Delete a threshold suggestion"""
    try:
        suggestion = ThresholdSuggestion.objects.get(id=suggestion_id)
        suggestion.delete()
        return Response({"message": f"Suggestion {suggestion_id} deleted successfully."})
    except ThresholdSuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found."}, status=status.HTTP_404_NOT_FOUND)
@api_view(['GET'])
def threshold_tuning_view(request):
    """
    Threshold Tuning API
    Reads latest ModSecurity CSV from uploads/ → finds best threshold → saves to DB
    """
    try:
        uploads_folder = "uploads"

        files = [
            f for f in os.listdir(uploads_folder)
            if f.lower().endswith(".csv") and ("modsec" in f.lower() or "log" in f.lower())
        ]

        if not files:
            return Response(
                {"error": "No uploaded traffic/log file found in uploads/. "
                          "Ask team to upload ModSecurity logs first."},
                status=400
            )

        files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(uploads_folder, f)), reverse=True)
        file_path = os.path.join(uploads_folder, files[0])

        df = pd.read_csv(file_path)

        if "anomaly_score" not in df.columns:
            return Response({"error": "Missing 'anomaly_score' column in CSV"}, status=400)

        if "action" not in df.columns:
            return Response({"error": "Missing 'action' column in CSV"}, status=400)

        df["actual_label"] = df["action"].apply(
            lambda x: 1 if str(x).lower() in ["blocked", "denied", "intercepted"] else 0
        )
        df["score"] = df["anomaly_score"].astype(float)

        best_threshold, best_accuracy = 0, 0
        for th in np.arange(0, 20.0, 1.0):  # anomaly score generally 0–20+
            df["predicted"] = (df["score"] >= th).astype(int)
            TP = ((df["actual_label"] == 1) & (df["predicted"] == 1)).sum()
            TN = ((df["actual_label"] == 0) & (df["predicted"] == 0)).sum()
            FP = ((df["actual_label"] == 0) & (df["predicted"] == 1)).sum()
            FN = ((df["actual_label"] == 1) & (df["predicted"] == 0)).sum()

            acc = (TP + TN) / (TP + TN + FP + FN + 1e-6)
            if acc > best_accuracy:
                best_accuracy, best_threshold = acc, th

        suggestion = ThresholdSuggestion.objects.create(value=best_threshold)

        return Response({
            "message": "Threshold tuning completed successfully.",
            "file_used": files[0],
            "best_threshold": round(best_threshold, 2),
            "accuracy": round(best_accuracy, 3),
            "records_tested": len(df),
            "saved_id": suggestion.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(['GET'])
def list_threshold_suggestions(request):
    """List all threshold suggestions"""
    suggestions = ThresholdSuggestion.objects.all().order_by('-created_at')
    data = [
        {
            "id": s.id,
            "value": s.value,
            "approved": s.approved,
            "applied": s.applied,
            "created_at": s.created_at,
        }
        for s in suggestions
    ]
    return Response({"suggestions": data}, status=status.HTTP_200_OK)


@api_view(['POST'])
def approve_threshold_suggestion(request, suggestion_id):
    """Approve and apply selected threshold"""
    try:
        suggestion = ThresholdSuggestion.objects.get(id=suggestion_id)
        suggestion.approved = True
        suggestion.applied = True
        suggestion.save()
        return Response({"message": f"Suggestion {suggestion_id} approved successfully."})

    except ThresholdSuggestion.DoesNotExist:
        return Response({"error": "Suggestion not found."}, status=status.HTTP_404_NOT_FOUND)
