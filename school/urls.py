from django.urls import path
from . import views

urlpatterns = [
    path('', views.mainpage, name="index"),
    path('account/<randomid>/delete', views.deleteaccount, name="deleteaccount"),
    path('account/edit/', views.editaccount, name="editaccount"),
    path('account/changepassword/', views.changepassword, name="changepassword"),
    path('account/', views.useraccount, name="useraccount"),
    path('schools/', views.schooldisplay, name="schooldisplay"),
    path('school/add/', views.addschool, name="addschool"),
    path('school/<randomid>/edit/', views.editschool, name="editschool"),
    path('school/<randomid>/delete/', views.deleteschool, name="deleteschool"),
    path('school/<randomid>/', views.schoolview, name="schoolview"),
    path('school/<randomid>/stream/', views.streamsview, name="streamview"),
    path('school/<randomid>/stream/add/', views.streamsadd, name="addstream"),
    path('school/<randomid>/stream/<streamslug>/edit/', views.streamsedit, name="editstream"),
    path('school/<randomid>/stream/<streamslug>/delete/', views.streamsdelete, name="deletestreams"),
    path('school/<randomid>/teacher/', views.teachersview, name="teacherview"),
    path('school/<randomid>/teacher/add/', views.teacheradd, name="addteacher"),
    path('school/<randomid>/teacher/<teacherrandomid>/edit/', views.teacheredit, name="editteacher"),
    path('school/<randomid>/teacher/<teacherrandomid>/delete/', views.teacherdelete, name="deleteteachers"),
    path('school/<randomid>/subject/', views.subjectsview, name="subjectview"),
    path('school/<randomid>/subject/add/', views.subjectsadd, name="addsubject"),
    path('school/<randomid>/subject/<subjectslug>/edit/', views.subjectsedit, name="editsubject"),
    path('school/<randomid>/subject/<subjectslug>/delete/', views.subjectsdelete, name="deletesubject"),
]