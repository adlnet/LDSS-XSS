# Generated by Django 4.2.17 on 2024-12-13 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20230901_1454'),
    ]

    operations = [
        migrations.AlterField(
            model_name='term',
            name='mapping',
            field=models.ManyToManyField(blank=True, to='core.term'),
        ),
    ]