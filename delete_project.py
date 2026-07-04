import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Project

def run():
    projects = Project.objects.filter(name__icontains="paramynd saas")
    count = projects.count()
    if count > 0:
        projects.delete()
        print(f"Deleted {count} project(s) matching 'paramynd saas'.")
    else:
        print("No project found matching 'paramynd saas'.")

if __name__ == '__main__':
    run()
