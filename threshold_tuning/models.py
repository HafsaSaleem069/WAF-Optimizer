from django.db import models

class ThresholdSuggestion(models.Model):
    """Stores AI-generated threshold tuning suggestions"""
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    applied = models.BooleanField(default=False)

    def __str__(self):
        return f"Threshold {self.value} (Approved: {self.approved})"