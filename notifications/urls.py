from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='detail'),

    # Yahan se shuru ka '/' hata diya gaya hai
    path('mark-read/<uuid:pk>/', views.MarkAsReadView.as_view(), name='mark_read'),

    path('mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark_all_read'),
    path('archive/<uuid:pk>/', views.ArchiveNotificationView.as_view(), name='archive'),
    path('count/', views.NotificationCountView.as_view(), name='count'),
]
