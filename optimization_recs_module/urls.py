from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import core analysis views AND the new optimization view
from .views import RuleAnalysisSessionViewSet, analyze_rules, get_analysis_session, api_apply_optimization 

router = DefaultRouter()
# /sessions/ (GET, POST, etc.)
router.register(r'sessions', RuleAnalysisSessionViewSet, basename='session')


urlpatterns = [
    # 1. Session Management (CRUD)
    path('', include(router.urls)),
    
    # 2. Core Rule Analysis Endpoints
    path('analyze/', analyze_rules, name='analyze-rules'), # POST: Start analysis
    path('session/<int:session_id>/', get_analysis_session, name='get-analysis-session'), # GET: Retrieve session details
    
    # 3. Optimization Application Endpoint (NEW)
    path('optimize/apply/', api_apply_optimization, name='apply-optimization'), # POST: Apply AI suggestion
]