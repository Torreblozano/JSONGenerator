from django.db import models
from django.contrib.auth.models import User

class Idata(models.Model):
    #TO JSON
    AssetName = models.TextField()
    AssetDescription = models.CharField(max_length=1000)
    SavePath = models.TextField(default='')
    CurrentVersion = models.PositiveIntegerField(default = 0)
    updated_at = models.DateTimeField(blank=True, null=True)

    # NOT TO JSON
    level = models.PositiveIntegerField()
    path = models.TextField()
    pathRoot = models.TextField(default='')
    isDirectory = models.BooleanField(default = False)
    needUpdate = models.BooleanField(default=False)

    def __str__(self):
        return self.AssetName

    class Meta:
        ordering = ['-isDirectory']


class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class SavedJSONS(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.TextField()
    path = models.TextField()