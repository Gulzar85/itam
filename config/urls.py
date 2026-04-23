from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from requests.views import RequestDashboardView
from core.views import GlobalSearchView

urlpatterns = [
    path('', RequestDashboardView.as_view(), name='dashboard'),
    path('admin/', admin.site.urls),
    path('inventory/', include('equipment.urls')),
    path('accounts/', include('accounts.urls')),
    path('notifications/', include('notifications.urls')),
    path('settings/', include('core.urls')),
    path('requests/', include('requests.urls')),
    path('api/search/', GlobalSearchView.as_view(), name='global_search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)