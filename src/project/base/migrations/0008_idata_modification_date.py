# Generated by Django 5.0.7 on 2024-07-19 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_uploadedfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='idata',
            name='modification_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
