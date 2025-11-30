from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponse
urlpatterns = [
    path('', lambda req: redirect('api/')),
    path('admin/', admin.site.urls),
    path('api/', include('data_management.urls')),
    path('api/', include('rule_analysis.urls')),
    path('api/', include('threshold_tuning.urls')),
    path('api/', include('optimization_recs_module.urls')),
    path('api/', include('false_positive_reduction.urls')),  # ✅ Add this line
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
