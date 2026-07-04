from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.board, name='board'),
    path('sprint/create/', views.create_sprint, name='create_sprint'),
    path('sprint/<int:sprint_id>/update-position/', views.update_sprint_position, name='update_sprint_position'),
    path('task/create/', views.create_task, name='create_task'),
    path('task/<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
    path('task/<int:task_id>/update-position/', views.update_task_position, name='update_task_position'),
    path('task/<int:task_id>/update-notes/', views.update_task_notes, name='update_task_notes'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('task/link-sprint/', views.link_task_to_sprint, name='link_task_to_sprint'),
    path('project/<int:project_id>/update-position/', views.update_project_position, name='update_project_position'),
    # Legacy kept for compat
    path('task/link/', views.link_tasks, name='link_tasks'),
    path('task/unlink/', views.unlink_tasks, name='unlink_tasks'),
]
