from django.urls import path

from . import views

urlpatterns = [
    path('school/<randomid>/timetable/', views.timetablesview, name="timetablesview"),
    path('school/<randomid>/timetable/<timetableid>/edit/', views.edittimetable, name="edittimetable"),
    path('school/<randomid>/timetable/<timetableid>/delete/', views.deletetimetable, name="deletetimetable"),
    path('school/<randomid>/timetable/<timetableid>/', views.timetablesingroup, name="timetablesingroup"),
    path('school/<randomid>/checktimetable/', views.timetablecheck, name="timetablecheck"),
    path('school/<randomid>/generatetimetable/', views.generatetimetable, name="generatetimetable"),
    path('school/<randomid>/timetable/<timetableid>/view/<classlug>/', views.onetimetable, name="onetimetable"),
    path('school/<randomid>/timetable/<timetableid>/view/<classlug>/pdf/', views.pdftimetable, name="pdftimetable"),
]