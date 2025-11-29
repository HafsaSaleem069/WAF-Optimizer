# rule_analysis/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
#from .views import RuleAnalysisSessionViewSet, analyze_rules
from .ranking_views import generate_rule_ranking, get_ranking_session, get_ranking_comparison, approve_ranking_session
from .hit_count_views import update_rule_hit_counts, get_hit_count_dashboard, get_rule_hit_details
from .performance_views import analyze_rule_performance, get_performance_snapshot, get_rule_performance_dashboard

router = DefaultRouter()
#router.register(r'sessions', RuleAnalysisSessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
    
    # Rule analysis endpoints
    #path('analyze/', analyze_rules, name='analyze-rules'),
    
    # Rule ranking endpoints (FR05)
    path('ranking/generate/', generate_rule_ranking, name='generate-ranking'),
    path('ranking/session/<int:session_id>/', get_ranking_session, name='get-ranking-session'),
    path('ranking/comparison/<int:session_id>/', get_ranking_comparison, name='get-ranking-comparison'),
    path('ranking/approve/<int:session_id>/', approve_ranking_session, name='approve-ranking'),
    
    # FR03-01 Hit Counting endpoints
    path('hit-counts/update/', update_rule_hit_counts, name='update-hit-counts'),
    path('hit-counts/dashboard/', get_hit_count_dashboard, name='hit-count-dashboard'),
    path('hit-counts/rule/<str:rule_id>/', get_rule_hit_details, name='rule-hit-details'),
    
    # FR03 Performance endpoints
    path('performance/analyze/', analyze_rule_performance, name='analyze-performance'),
    path('performance/snapshot/<int:snapshot_id>/', get_performance_snapshot, name='get-performance-snapshot'),
    path('performance/dashboard/', get_rule_performance_dashboard, name='performance-dashboard'),
    
]