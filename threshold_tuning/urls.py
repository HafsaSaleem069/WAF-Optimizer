from django.urls import path
from . import views
from .views import threshold_tuning_view

urlpatterns = [
    path('threshold_tuning/', threshold_tuning_view, name='threshold_tuning'),
    path('threshold_suggestions/', views.list_threshold_suggestions, name='list-threshold-suggestions'),
    path('threshold_suggestions/approve/<int:suggestion_id>/', views.approve_threshold_suggestion, name='approve-threshold'),
    path('threshold_suggestions/delete/<int:suggestion_id>/', views.delete_threshold_suggestion, name='delete-threshold'),
]