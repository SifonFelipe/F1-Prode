# Generated by Django 5.0.6 on 2025-04-03 23:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='year',
            field=models.IntegerField(default=2025),
        ),
        migrations.AlterField(
            model_name='driver',
            name='number',
            field=models.IntegerField(),
        ),
    ]
