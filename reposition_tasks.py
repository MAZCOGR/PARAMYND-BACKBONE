import django, os, random
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from projects.models import Project, Sprint, Task

projects = list(Project.objects.order_by('id'))
for i, p in enumerate(projects):
    p.x_position = 100 + i * 340
    p.y_position = 40
    p.save()
    print(f'Project {p.id} "{p.name}" -> ({int(p.x_position)}, {int(p.y_position)})')

sprints = list(Sprint.objects.order_by('id'))
for i, s in enumerate(sprints):
    s.x_position = 60 + i * 290
    s.y_position = 280
    s.save()
    print(f'Sprint {s.id} "{s.name}" -> ({int(s.x_position)}, {int(s.y_position)})')

tasks = list(Task.objects.order_by('id'))
for i, t in enumerate(tasks):
    t.x_position = 40 + (i % 5) * 240
    t.y_position = 520 + (i // 5) * 160
    t.save()
    print(f'Task {t.id} "{t.title}" -> ({int(t.x_position)}, {int(t.y_position)})')

print('Done!')
