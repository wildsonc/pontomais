# Generated by Django 4.0.2 on 2022-02-17 14:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_telegramgroup_options_history_date_time_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='history',
            unique_together={('name', 'date_time')},
        ),
    ]
