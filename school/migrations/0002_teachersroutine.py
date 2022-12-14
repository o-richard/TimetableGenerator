# Generated by Django 4.0.5 on 2022-07-03 15:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeachersRoutine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Sunday', 'Sunday'), ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday')], max_length=20)),
                ('starttime', models.TimeField()),
                ('endtime', models.TimeField()),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school.teachers')),
            ],
            options={
                'verbose_name': 'Teacher Routine',
                'verbose_name_plural': 'Teacher Routines',
            },
        ),
    ]
