# Generated by Django 3.2.25 on 2024-11-04 16:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uid', '0004_auto_20241031_1227'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LastGeneratedUID',
        ),
        migrations.DeleteModel(
            name='LCVTermDjangoModel',
        ),
        migrations.DeleteModel(
            name='UIDCounterDjangoModel',
        ),
        migrations.RemoveField(
            model_name='providerdjangomodel',
            name='uid',
        ),
    ]