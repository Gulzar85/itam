from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    # Equipment CRUD
    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/<uuid:pk>/', views.EquipmentDetailView.as_view(),
         name='equipment_detail'),
    path('equipment/create/', views.EquipmentCreateView.as_view(),
         name='equipment_create'),
    path('equipment/<uuid:pk>/update/',
         views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path('equipment/<uuid:pk>/delete/',
         views.EquipmentDeleteView.as_view(), name='equipment_delete'),

    # Is line ko update kiya gaya hai taakay template ke {% url 'equipment:update_status' %} se match kare
    path('equipment/<uuid:pk>/status/',
         views.EquipmentStatusUpdateView.as_view(), name='update_status'),

    # Vendor CRUD
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/<uuid:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('vendors/create/', views.VendorCreateView.as_view(), name='vendor_create'),
    path('vendors/<uuid:pk>/update/',
         views.VendorUpdateView.as_view(), name='vendor_update'),
    path('vendors/<uuid:pk>/delete/',
         views.VendorDeleteView.as_view(), name='vendor_delete'),

    # Brand CRUD
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/<uuid:pk>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<uuid:pk>/update/',
         views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<uuid:pk>/delete/',
         views.BrandDeleteView.as_view(), name='brand_delete'),

    # Category CRUD
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<uuid:pk>/',
         views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/create/', views.CategoryCreateView.as_view(),
         name='category_create'),
    path('categories/<uuid:pk>/update/',
         views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<uuid:pk>/delete/',
         views.CategoryDeleteView.as_view(), name='category_delete'),

    # Legacy URL
    path('list/', views.EquipmentListView.as_view(), name='inventory_list'),
    path('dashboard/report/', views.DashboardReportView.as_view(),
         name='dashboard_report'),
    path('reports/comprehensive/', views.DashboardReportView.as_view(),
         name='comprehensive_report'),
]
