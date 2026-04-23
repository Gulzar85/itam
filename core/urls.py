from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Business Information
    path('business/', views.BusinessInfoDetailView.as_view(), name='business_info'),
    path('business/edit/', views.BusinessInfoUpdateView.as_view(),
         name='business_info_update'),

    # Social Media Links
    path('social-media/', views.SocialMediaListView.as_view(),
         name='social_media_list'),
    path('social-media/add/', views.SocialMediaCreateView.as_view(),
         name='social_media_create'),
    path('social-media/<int:pk>/edit/',
         views.SocialMediaUpdateView.as_view(), name='social_media_update'),
    path('social-media/<int:pk>/delete/',
         views.SocialMediaDeleteView.as_view(), name='social_media_delete'),
]
