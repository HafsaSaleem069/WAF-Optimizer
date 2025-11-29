from django.db import models

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('rules', 'WAF Rules File'),
        ('traffic', 'Traffic Data File'),
    ]

    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.PositiveIntegerField(default=0)
    supabase_path = models.CharField(max_length=255, blank=True, null=True)  # Path in Supabase bucket
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} - {self.filename}"
