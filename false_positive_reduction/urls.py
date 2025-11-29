# false_positive/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    analyze_false_positives,
    export_whitelist_csv,
)

router = DefaultRouter()

# You can later register ModelViewSets if needed
# e.g., router.register(r'sessions', RuleAnalysisSessionViewSet, basename='session')

urlpatterns = [
    path('analyzefalsepostive/', analyze_false_positives, name='analyze_false_positives'),
    path('export-whitelist/', export_whitelist_csv, name='export_whitelist_csv'),
    path('', include(router.urls)),
]
