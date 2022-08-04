from django.contrib import admin
from .models import *


class SchoolGroupsAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":("groupname",)}
    
admin.site.register(SchoolGroups, SchoolGroupsAdmin)

admin.site.register(Grouproutine)

class GroupbreaksAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":("breakname",)}
    
admin.site.register(Groupbreaks, GroupbreaksAdmin)

admin.site.register(Groupsubjects)

class GroupclassesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":("classname",)}
    
admin.site.register(Groupclasses, GroupclassesAdmin)

admin.site.register(Groupsubjectteachers)
admin.site.register(GroupSpecifiction)