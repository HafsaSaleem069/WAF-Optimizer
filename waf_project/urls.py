from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponse

urlpatterns = [
    # Root: lightweight landing or redirect to API
    path('', lambda req: redirect('api/')),
    path('admin/', admin.site.urls),
    path('api/', include('data_management.urls')),
    path('api/', include('rule_analysis.urls')),
    path('api/', include('threshold_tuning.urls')),
    path('api/', include('optimization_recs_module.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
