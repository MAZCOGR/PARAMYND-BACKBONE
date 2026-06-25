from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.logs_view, name='logs'),
    path('table/', views.logs_table_partial_view, name='logs_table'),
    path('api/<str:service_name>/', views.logs_api_view, name='logs_api'),
]
