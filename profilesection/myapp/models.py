from django.db import models

# Create your models here.

class Profile(models.Model):
    id=models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.TextField(blank=True)
    role = models.CharField(max_length=100, blank=True)
    team = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name