# Generated by Django 5.0.6 on 2025-04-23 23:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_customuser_points_yearscore_points'),
    ]

    operations = [
        migrations.DeleteModel(
            name='YearScore',
        ),
    ]
