# Generated by Django 5.2 on 2025-04-28 19:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0011_predictedpole'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predictedpole',
            name='driver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='predictions.driver'),
        ),
    ]
