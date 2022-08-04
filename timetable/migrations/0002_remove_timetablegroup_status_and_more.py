# Generated by Django 4.0.5 on 2022-07-06 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='timetablegroup',
            name='status',
        ),
        migrations.AddField(
            model_name='timetablebreaks',
            name='breakname',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='timetablegroup',
            name='datecreated',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]