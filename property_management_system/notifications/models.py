from django.db import models

from properties.models import Property


class Reminder(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

