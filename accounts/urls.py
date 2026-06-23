from django.urls import path
from . import views
from . import user_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # User Management
    path('users/', user_views.user_list_view, name='user_list'),
    path('users/create/', user_views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', user_views.user_update_view, name='user_update'),
    path('users/<int:pk>/delete/', user_views.user_delete_view, name='user_delete'),
    path('users/<int:pk>/password/', user_views.user_password_reset_view, name='user_password_reset'),

    # Role Matrix
    path('roles/', user_views.role_matrix_view, name='role_matrix'),
]
