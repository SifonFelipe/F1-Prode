# Generated by Django 5.2 on 2025-05-26 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0027_alter_session_options_sessionlineup'),
    ]

    operations = [
        migrations.AddField(
            model_name='grandprix',
            name='lineup_associated',
            field=models.BooleanField(default=False),
        ),
    ]
