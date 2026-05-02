from django.urls import path
from .views import (
    RequestDashboardView,
    RequestCreateView,
    RequestActionView,
    RequestDetailView,
    AssignmentCreateView,
    ManagerApprovalView,
    RequestAssignmentView,
    ProcessMaintenanceView,
    CompleteMaintenanceView,
    MyEquipmentView,
)

app_name = 'requests'

urlpatterns = [
    path('', RequestDashboardView.as_view(), name='dashboard'),
    path('my-equipment/', MyEquipmentView.as_view(), name='my_equipment'),
    path('new/', RequestCreateView.as_view(), name='create'),
    path('approvals/', ManagerApprovalView.as_view(), name='manager_approvals'),

    # Detail View
    path('<uuid:pk>/', RequestDetailView.as_view(), name='detail'),

    # Generic Actions (Approve/Reject)
    path('action/<uuid:pk>/', RequestActionView.as_view(), name='update_action'),

    # IT Admin Specific Actions
    path('<uuid:pk>/assign/', RequestAssignmentView.as_view(),
         name='assign_equipment'),
    path('assign-new/', AssignmentCreateView.as_view(),
         name='equipment_assign'),  # Name change for clarity

    # Maintenance / Repair Workflow
    path('<uuid:pk>/process-maintenance/',
         ProcessMaintenanceView.as_view(), name='process_maintenance'),

    path('<uuid:pk>/complete-maintenance/',
         CompleteMaintenanceView.as_view(), name='complete_maintenance'),  # <-- Yeh add kiya hai
]
