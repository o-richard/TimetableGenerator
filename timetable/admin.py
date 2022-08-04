from django.contrib import admin

from .models import *

class TimetablegroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":("timetablegroupname",)}

admin.site.register(Timetablegroup, TimetablegroupAdmin)

admin.site.register(Timetablebreaks)

admin.site.register(Timetablelessons)