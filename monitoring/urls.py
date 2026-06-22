from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.logs_view, name='logs'),
    path('api/<str:tenant_slug>/', views.logs_api_view, name='logs_api'),
]
