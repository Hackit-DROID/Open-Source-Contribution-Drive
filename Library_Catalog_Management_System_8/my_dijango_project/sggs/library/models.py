from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    version = models.IntegerField(default=0)

    class Meta:
        app_label = 'library'

    def __str__(self):
        return f"{self.title} by {self.author}"