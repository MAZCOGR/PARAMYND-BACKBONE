from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('', views.tenant_list_view, name='list'),
    path('new/', views.tenant_create_view, name='create'),
    path('<uuid:pk>/', views.tenant_detail_view, name='detail'),
    path('<uuid:pk>/deploy/', views.tenant_deploy_view, name='deploy'),
    path('<uuid:pk>/rollback/', views.tenant_rollback_view, name='rollback'),
    path('<uuid:pk>/status/', views.tenant_status_view, name='status'),
    path('builds/', views.builds_view, name='builds'),
]
