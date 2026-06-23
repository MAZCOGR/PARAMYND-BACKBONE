from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.logs_view, name='logs'),
    path('api/<str:service_name>/', views.logs_api_view, name='logs_api'),
]
