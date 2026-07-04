import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Project

def run():
    p1, created1 = Project.objects.get_or_create(name='Backbone', defaults={'description': 'Paramynd Backbone infrastructure'})
    p2, created2 = Project.objects.get_or_create(name='SaaS', defaults={'description': 'Paramynd SaaS Application'})
    
    if created1:
        print(f"Created project: {p1.name}")
    if created2:
        print(f"Created project: {p2.name}")
    print("Projects are ready!")

if __name__ == '__main__':
    run()
