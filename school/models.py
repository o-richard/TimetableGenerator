from statistics import mode
from turtle import color
from django.db import models
from django.contrib.auth.models import AbstractUser 
from django.conf import settings
from django.utils.text import slugify
from colorfield.fields import ColorField
from .validators import validate_logo

# Store info on registred users
class User(AbstractUser):
    randomid = models.CharField(max_length=60, unique=True)
    
    def __str__(self):
        return f"{self.username}"


# Store info on schools by a particular users
class School(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    schoolname = models.CharField(max_length=200)
    randomid = models.CharField(max_length=60, unique=True)
    schoollogo = models.ImageField(upload_to='logo', validators=[validate_logo], default='logo.jpg')
        
    class Meta:
        verbose_name = ("School")
        verbose_name_plural = ("Schools")

    def __str__(self):
        return f"{self.schoolname} by {self.user.id}"

# Store info on subjects by a given school Has a method to check if an object can be deleted.
class Subjects(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    subjectname = models.CharField(max_length=100)
    slug = models.SlugField()
    color = ColorField()

    class Meta:
        verbose_name = ("Subject")
        verbose_name_plural = ("Subjects")

    def __str__(self):
        return f"{self.subjectname}"

    # Slugify the subjectname as you save
    def save(self, *args, **kwargs):
        self.slug = slugify(self.subjectname)
        super(Subjects, self).save(*args, **kwargs)

    # Check if can delete this subject
    def ifcandelete(self):
        from timetable.models import Timetablelessons
        check1 = Timetablelessons.objects.filter(subject__id=self.id).count()

        # If there are timetable models using this subject
        if (check1 > 0):
            return False
        else:
            return True

# Store info on teachers by a given . Has a method to check if an object can be deleted.
class Teachers(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    teachername = models.CharField(max_length=100)
    randomid = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = ("Teacher")
        verbose_name_plural = ("Teachers")

    def __str__(self):
        return f"{self.teachername}"

    # Check if can delete this teacher
    def ifcandelete(self):
        from timetable.models import Timetablelessons
        check1 = Timetablelessons.objects.filter(teacher__id=self.id).count()

        # If there are timetable models using this teacher
        if (check1 > 0):
            return False
        else:
            return True

# Store info on routine by a given teacher.
class TeachersRoutine(models.Model):
    teacher = models.ForeignKey(Teachers, on_delete=models.CASCADE)
    day = models.CharField(max_length=20, choices=settings.DAYS)
    starttime = models.TimeField()
    endtime = models.TimeField()

    class Meta:
        verbose_name = ("Teacher Routine")
        verbose_name_plural = ("Teacher Routines")

    def __str__(self):
        return f"{self.teacher.teachername} Routine on {self.day}"

# Store info on streams by a given school. Has a method to check if an object can be deleted.
class Streams(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    streamname = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        verbose_name = ("Stream")
        verbose_name_plural = ("Streams")

    def __str__(self):
        return f"{self.streamname}"

    # Slugify the streamname as you save
    def save(self, *args, **kwargs):
        self.slug = slugify(self.streamname)
        super(Streams, self).save(*args, **kwargs)

    # Check if can delete this stream
    def ifcandelete(self):
        from timetable.models import Timetablelessons, Timetablebreaks
        check1 = Timetablelessons.objects.filter(theclass__stream__id=self.id).count()
        check2 = Timetablebreaks.objects.filter(theclass__stream__id=self.id).count()

        # If there are timetable models using this stream
        if (check1 > 0) or (check2 > 0):
            return False
        else:
            return True