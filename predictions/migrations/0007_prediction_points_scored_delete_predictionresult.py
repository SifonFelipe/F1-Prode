# Generated by Django 5.0.6 on 2025-04-07 23:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0006_alter_predictedposition_options_alter_result_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediction',
            name='points_scored',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.DeleteModel(
            name='PredictionResult',
        ),
    ]
