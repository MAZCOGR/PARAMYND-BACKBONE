from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    x_position = models.FloatField(default=100.0)
    y_position = models.FloatField(default=40.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Sprint(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    x_position = models.FloatField(default=100.0)
    y_position = models.FloatField(default=280.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_TODO       = 'TODO'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_TESTED      = 'TESTED'
    STATUS_DEPLOYED    = 'DEPLOYED'
    STATUS_DONE        = 'DONE'

    STATUS_CHOICES = [
        (STATUS_TODO,        'À faire'),
        (STATUS_IN_PROGRESS, 'En cours'),
        (STATUS_TESTED,      'Testé'),
        (STATUS_DEPLOYED,    'Déployé'),
        (STATUS_DONE,        'Terminé'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    sprint = models.ForeignKey('Sprint', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')

    # Graph View Fields
    x_position = models.FloatField(default=100.0)
    y_position = models.FloatField(default=520.0)
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependents')

    notes = models.TextField(blank=True)
    expected_finish_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
