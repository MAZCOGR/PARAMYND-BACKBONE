from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Task, Project, Sprint
import random


def board(request):
    projects = Project.objects.all().order_by('id')
    sprints = Sprint.objects.select_related('project').all().order_by('id')
    tasks = Task.objects.select_related('project', 'sprint').all().order_by('id')

    # Auto-layout: place projects at top row, sprints in middle, tasks at bottom
    # Only for newly created items at default position
    for i, p in enumerate(projects):
        if p.x_position == 100.0 and p.y_position == 40.0:
            p.x_position = 80 + i * 320
            p.y_position = 40
            p.save()

    for i, s in enumerate(sprints):
        if s.x_position == 100.0 and s.y_position == 280.0:
            s.x_position = 80 + i * 280
            s.y_position = 280
            s.save()

    for i, t in enumerate(tasks):
        if t.x_position == 100.0 and t.y_position == 520.0:
            t.x_position = 60 + (i % 5) * 250
            t.y_position = 520 + (i // 5) * 160
            t.save()

    return render(request, 'projects/board.html', {
        'projects': projects,
        'sprints': sprints,
        'tasks': tasks,
    })


@require_POST
def create_sprint(request):
    name = request.POST.get('name')
    project_id = request.POST.get('project_id')
    if name and project_id:
        project = get_object_or_404(Project, id=project_id)
        Sprint.objects.create(name=name, project=project)
    return redirect('projects:board')


@require_POST
def create_task(request):
    title = request.POST.get('title')
    project_id = request.POST.get('project_id')
    sprint_id = request.POST.get('sprint_id') or None
    notes = request.POST.get('notes', '')
    expected_finish_date = request.POST.get('expected_finish_date') or None

    if title and project_id:
        project = get_object_or_404(Project, id=project_id)
        sprint = get_object_or_404(Sprint, id=sprint_id) if sprint_id else None
        Task.objects.create(
            title=title,
            project=project,
            sprint=sprint,
            status=Task.STATUS_TODO,
            notes=notes,
            expected_finish_date=expected_finish_date,
            x_position=100.0 + random.randint(0, 800),
            y_position=520.0 + random.randint(0, 200),
        )
    return redirect('projects:board')


@require_POST
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    new_status = request.POST.get('status')
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        task.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@require_POST
def update_task_position(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    try:
        task.x_position = float(request.POST.get('x', task.x_position))
        task.y_position = float(request.POST.get('y', task.y_position))
        task.save()
        return JsonResponse({'success': True})
    except ValueError:
        return JsonResponse({'success': False}, status=400)


@require_POST
def update_task_notes(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    notes = request.POST.get('notes', '')
    task.notes = notes
    task.save()
    return JsonResponse({'success': True})


@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return JsonResponse({'success': True})


@require_POST
def update_sprint_position(request, sprint_id):
    sprint = get_object_or_404(Sprint, id=sprint_id)
    try:
        sprint.x_position = float(request.POST.get('x', sprint.x_position))
        sprint.y_position = float(request.POST.get('y', sprint.y_position))
        sprint.save()
        return JsonResponse({'success': True})
    except ValueError:
        return JsonResponse({'success': False}, status=400)


@require_POST
def update_project_position(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    try:
        project.x_position = float(request.POST.get('x', project.x_position))
        project.y_position = float(request.POST.get('y', project.y_position))
        project.save()
        return JsonResponse({'success': True})
    except ValueError:
        return JsonResponse({'success': False}, status=400)


@require_POST
def link_task_to_sprint(request):
    task_id = request.POST.get('task_id')
    sprint_id = request.POST.get('sprint_id')
    task = get_object_or_404(Task, id=task_id)
    if sprint_id:
        sprint = get_object_or_404(Sprint, id=sprint_id)
        task.sprint = sprint
    else:
        task.sprint = None
    task.save()
    return JsonResponse({'success': True})


# Legacy endpoints (kept for backward compat)
@require_POST
def link_tasks(request):
    return JsonResponse({'success': True})

@require_POST
def unlink_tasks(request):
    return JsonResponse({'success': True})
