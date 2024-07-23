from django.db import models
from django.contrib.auth.models import User

class Idata(models.Model):
    usuario = models.ForeignKey(User, on_delete= models.CASCADE, null=True)
    name = models.TextField()
    level = models.PositiveIntegerField()
    path = models.TextField()
    pathRoot = models.TextField(default='')
    description = models.CharField(max_length=1000)
    isDirectory = models.BooleanField(default = False)
    Exclude = models.BooleanField(default=False)
    SavePath = models.TextField(default='')
    modification_date = models.DateTimeField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-isDirectory']


class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)