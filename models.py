# models.py - Modele reprezentujące zadania i podzadania
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from projects.models import Project

User = get_user_model()


class Task(models.Model):
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completion_percentage = models.IntegerField(default=0)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'due_date', 'created_at']

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    def update_completion_from_subtasks(self):
        """Update task completion percentage based on subtasks"""
        subtasks = self.subtasks.all()
        if not subtasks:
            return  # No subtasks, keep current completion value

        total_subtasks = subtasks.count()
        completed_subtasks = subtasks.filter(status='done').count()

        # Calculate weighted completion based on subtasks
        total_weight = sum(subtask.estimated_hours or 1 for subtask in subtasks)
        weighted_completion = 0

        for subtask in subtasks:
            weight = subtask.estimated_hours or 1
            subtask_completion = 100 if subtask.status == 'done' else subtask.completion_percentage
            weighted_completion += (weight / total_weight) * subtask_completion

        self.completion_percentage = int(weighted_completion)
        self.save(update_fields=['completion_percentage', 'last_updated'])

    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date:
            return False
        return self.due_date < timezone.now().date() and self.status != 'done'


class Subtask(models.Model):
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    completion_percentage = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.task.title} - {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update parent task completion when subtask changes
        self.task.update_completion_from_subtasks()
