# Generated by Django 3.2.25 on 2024-11-07 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uid', '0009_lcvtermdjangomodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='UIDRequestToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255, unique=True)),
                ('provider_name', models.CharField(max_length=255)),
                ('echelon', models.CharField(max_length=255)),
                ('termset', models.CharField(max_length=255)),
                ('uid', models.CharField(max_length=255)),
                ('uid_chain', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'UIDRequestToken',
                'verbose_name_plural': 'UIDRequestTokens',
            },
        ),
        migrations.AlterField(
            model_name='providerdjangomodel',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
