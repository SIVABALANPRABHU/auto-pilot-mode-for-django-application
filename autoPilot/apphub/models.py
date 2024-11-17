from django.db import models

class GeneratedApp(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class ModelField(models.Model):
    FIELD_TYPES = [
        ('CharField', 'CharField'),
        ('IntegerField', 'IntegerField'),
        ('BooleanField', 'BooleanField'),
        ('DateField', 'DateField'),
    ]

    app = models.ForeignKey(GeneratedApp, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=50)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    max_length = models.IntegerField(null=True, blank=True)  # For CharField
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.field_type})"

