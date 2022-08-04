from django.contrib import admin
from .models import *

admin.site.register(User)

admin.site.register(School)

admin.site.register(Subjects)

class TeacherRoutineInline(admin.StackedInline):
    model = TeachersRoutine
    extra = 0

class TeachersAdmin(admin.ModelAdmin):
    inlines = [TeacherRoutineInline,]

admin.site.register(Teachers, TeachersAdmin)

class StreamsAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":("streamname",)}
    
admin.site.register(Streams, StreamsAdmin)