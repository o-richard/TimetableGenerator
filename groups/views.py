from turtle import update
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from school.models import School
from school.models import Subjects
from .models import GroupSpecifiction, Groupbreaks, Groupclasses, Grouproutine, Groupsubjects, Groupsubjectteachers, SchoolGroups
from .forms import GroupsForm, ClassForm, RoutineForm, BreaksForm, GroupSubjectsForm, LessonForm, GroupSpecifictionForm

# View all Groups In Agiven School
@login_required
def groupdisplay(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Get the subjects of this school
    schoolgroups = SchoolGroups.objects.filter(school__randomid=randomid)
    return render(request, "frontend/school/groupsview.html", {"schoolgroups":schoolgroups, "theschool":theschool})

# Add a Group for a given school
@login_required
def groupadd(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Store title of page
    thelabel = 'Add A Group'
    # initialize the form
    groupform = GroupsForm(theschool=theschool, thestate='Add', groupname=None)

    # Set form action
    groupform.helper.form_action = reverse('addgroup', kwargs={"randomid":randomid})

    if request.method == 'POST':
        groupform = GroupsForm(request.POST,theschool=theschool, thestate='Add', groupname=None)
        if groupform.is_valid():
            # Save the group
            thegroup = groupform.save(commit=False)
            thegroup.school = theschool
            thegroup.save()
            messages.success(request, "You successfully added a group")
            gotourl = reverse("groupview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":groupform, "theschool":theschool,"thelabel":thelabel})

# Edit a particular group
def groupedit(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Group'
    # initialize the form
    # Store current information in DB
    update_initial = {}
    update_initial["groupname"] = thegroup.groupname
    update_initial["lessonduration"] = thegroup.lessonduration
    groupform = GroupsForm(theschool=theschool, thestate='Edit', groupname=thegroup.groupname, data=update_initial)

    # Set form action
    groupform.helper.form_action = reverse('editgroup', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        groupform = GroupsForm(request.POST, theschool=theschool, thestate='Edit', groupname=thegroup.groupname)
        if groupform.is_valid():
            # Save the group changes
            thegroup.groupname = groupform.cleaned_data['groupname']
            thegroup.save()
            messages.success(request, "You successfully edited a group")
            gotourl = reverse("groupview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":groupform, "theschool":theschool,"thelabel":thelabel})

# Delete a group
@login_required
def groupdelete(request, randomid, groupslug):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    thegroup.delete()
    gotourl = reverse("groupview", kwargs={"randomid":randomid})
    messages.success(request, "You successfully deleted a group")
    return redirect(gotourl)

# View a particular group
@login_required
def groupview(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Group details( A max of 3 each)
    classes = Groupclasses.objects.filter(group__id=thegroup.id)[:3]
    breaks = Groupbreaks.objects.filter(group__id=thegroup.id)[:3]
    routine = Grouproutine.objects.filter(group__id=thegroup.id)[:3]
    subjects = Groupsubjects.objects.filter(group__id=thegroup.id)[:3]
    lessons = Groupsubjectteachers.objects.filter(groupsubjects__group__id=thegroup.id)[:3]
    specifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=thegroup.id)[:3]
    
    return render(request, "frontend/groups/groupsdisplay.html", {"theschool":theschool, "thegroup":thegroup, "classes":classes,"breaks":breaks,"routines":routine,"subjects":subjects,"lessons":lessons, "specifications":specifications})

# Show all classes of a particular group
@login_required
def classview(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Show the classes
    classes = Groupclasses.objects.filter(group__id=thegroup.id)
    return render(request, "frontend/groups/classesview.html", {"theschool":theschool, "thegroup":thegroup, "classes":classes})

# Add a class
@login_required
def classadd(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Add A Class'
    # initialize the form
    classform = ClassForm(theschool=theschool, thegroup=thegroup, thestate='Add', classname=None, theclassteacher=None, stream=None)

    # Set form action
    classform.helper.form_action = reverse('addclass', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        classform = ClassForm(request.POST, theschool=theschool, thegroup=thegroup, thestate='Add', classname=None, theclassteacher=None, stream=None)
        if classform.is_valid():
            # Save the class
            theclass = classform.save(commit=False)
            theclass.group = thegroup
            theclass.save()
            messages.success(request, "You successfully added a class")
            gottourl = reverse("classview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":classform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Edit a class
@login_required
def classedit(request, randomid, groupslug, classslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Class'
    # Check if a class exists
    theclass = get_object_or_404(Groupclasses, group__id=thegroup.id, slug=classslug)
    # initialize the form
    # Store initial data
    update_initial = {}
    update_initial['stream'] = theclass.stream
    update_initial['classname'] = theclass.classname
    update_initial['classteacher'] = theclass.classteacher
    classform = ClassForm(theschool=theschool, thegroup=thegroup, thestate='Edit', classname=theclass.classname, theclassteacher=theclass.classteacher, stream=theclass.stream.streamname, data=update_initial)

    # Set form action
    classform.helper.form_action = reverse('editclass', kwargs={"randomid":randomid, "groupslug":groupslug, "classslug":classslug})

    if request.method == 'POST':
        classform = ClassForm(request.POST, theschool=theschool, thegroup=thegroup, thestate='Edit', classname=theclass.classname, theclassteacher=theclass.classteacher, stream=theclass.stream.streamname)
        if classform.is_valid():
            # Save the class
            theclass.classname = classform.cleaned_data['classname']
            theclass.stream = classform.cleaned_data['stream']
            theclass.classteacher = classform.cleaned_data['classteacher']
            theclass.save()
            messages.success(request, "You successfully edited a class")
            gottourl = reverse("classview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":classform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Delete a class
@login_required
def classdelete(request, randomid, groupslug, classslug):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Check if a class exists
    theclass = get_object_or_404(Groupclasses, group__id=thegroup.id, slug=classslug)
    if theclass.ifcandelete() == True:
        theclass.delete()
        messages.success(request, "You successfully deleted a class")
    else:
        messages.success(request, "Sorry, you can not delete this class. Delete the timetable using with class first")
    gottourl = reverse("classview", kwargs={"randomid":randomid, "groupslug":groupslug})
    return redirect(gottourl)

# Show all routine of a group
@login_required
def routineview(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Show the routines
    routine = Grouproutine.objects.filter(group__id=thegroup.id)
    return render(request, "frontend/groups/routineview.html", {"theschool":theschool, "thegroup":thegroup, "routines":routine})

# Add a routine
@login_required
def routineadd(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Add A Routine'
    # initialize the form
    routineform = RoutineForm(thegroup=thegroup, thestate='Add', initialday=None)

    # Set form action
    routineform.helper.form_action = reverse('addroutine', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        routineform = RoutineForm(request.POST, thegroup=thegroup, thestate='Add', initialday=None)
        if routineform.is_valid():
            # Save the routine
            theroutine = routineform.save(commit=False)
            theroutine.group = thegroup
            theroutine.save()
            messages.success(request, "You successfully added a routine")
            gottourl = reverse("routineview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":routineform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Edit a routine
@login_required
def routineedit(request, randomid, groupslug, routineid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Routine'
    # Check if a routine exists
    theroutine = get_object_or_404(Grouproutine, id=routineid)
    # initialize the form
    # Store initial data
    update_initial = {}
    update_initial['day'] = theroutine.day
    update_initial['starttime'] = theroutine.starttime
    update_initial['endtime'] = theroutine.endtime
    # initialize the form
    routineform = RoutineForm(thegroup=thegroup, thestate='Edit', initialday=theroutine.day, data=update_initial)

    # Set form action
    routineform.helper.form_action = reverse('editroutine', kwargs={"randomid":randomid, "groupslug":groupslug, "routineid":routineid})

    if request.method == 'POST':
        routineform = RoutineForm(request.POST,thegroup=thegroup, thestate='Edit', initialday=theroutine.day)
        if routineform.is_valid():
            # Save the routine
            theroutine.day = routineform.cleaned_data['day']
            theroutine.starttime = routineform.cleaned_data['starttime']
            theroutine.endtime = routineform.cleaned_data['endtime']
            theroutine.save()
            messages.success(request, "You successfully edited a routine")
            gottourl = reverse("routineview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":routineform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Delete a routine
@login_required
def routinedelete(request, randomid, groupslug, routineid):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Check if a routine exists
    theroutine = get_object_or_404(Grouproutine, id=routineid)
    theroutine.delete()
    gottourl = reverse("routineview", kwargs={"randomid":randomid, "groupslug":groupslug})
    messages.success(request, "You successfully deleted a routine")
    return redirect(gottourl)

# Show all breaks of a group
@login_required
def breakview(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Show the breaks
    breaks = Groupbreaks.objects.filter(group__id=thegroup.id)
    return render(request, "frontend/groups/breaksview.html", {"theschool":theschool, "thegroup":thegroup, "breaks":breaks})

# Add a routine
@login_required
def breakadd(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Add A Break'
    # initialize the form
    breakform = BreaksForm(thegroup=thegroup,thestate=None,initialbreak=None)

    # Set form action
    breakform.helper.form_action = reverse('addbreak', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        breakform = BreaksForm(request.POST, thegroup=thegroup,thestate=None,initialbreak=None)
        if breakform.is_valid():
            # Save the break
            thebreak = breakform.save(commit=False)
            thebreak.group = thegroup
            thebreak.save()
            messages.success(request, "You successfully added a break")
            gottourl = reverse("breakview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":breakform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Edit a routine
@login_required
def breakedit(request, randomid, groupslug, breakid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Break'
    # Check if a break exists
    thebreak = get_object_or_404(Groupbreaks, group__id=thegroup.id, id=breakid)
    # initialize the form
    # Store initial data
    update_initial = {}
    update_initial['breakname'] = thebreak.breakname
    update_initial['day'] = thebreak.day
    update_initial['starttime'] = thebreak.starttime
    update_initial['endtime'] = thebreak.endtime
    # initialize the form
    breakform = BreaksForm(thegroup=thegroup,thestate='Edit',initialbreak=thebreak,data=update_initial)

    # Set form action
    breakform.helper.form_action = reverse('editbreak', kwargs={"randomid":randomid, "groupslug":groupslug, "breakid":breakid})

    if request.method == 'POST':
        breakform = BreaksForm(request.POST,thegroup=thegroup,thestate='Edit',initialbreak=thebreak)
        if breakform.is_valid():
            # Save the break
            thebreak.breakname = breakform.cleaned_data['breakname']
            thebreak.day = breakform.cleaned_data['day']
            thebreak.starttime = breakform.cleaned_data['starttime']
            thebreak.endtime = breakform.cleaned_data['endtime']
            thebreak.save()
            messages.success(request, "You successfully edited a break")
            gottourl = reverse("breakview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":breakform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Delete a break
@login_required
def breakdelete(request, randomid, groupslug, breakid):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Check if a break exists
    thebreak = get_object_or_404(Groupbreaks, group__id=thegroup.id, id=breakid)
    thebreak.delete()
    gottourl = reverse("breakview", kwargs={"randomid":randomid, "groupslug":groupslug})
    messages.success(request, "You successfully deleted a break")
    return redirect(gottourl)

# Show all subjects by group
@login_required
def groupsubjectsiew(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Show the subjects
    subjects = Groupsubjects.objects.filter(group__id=thegroup.id)
    return render(request, "frontend/groups/subjectsview.html", {"theschool":theschool, "thegroup":thegroup, "subjects":subjects})

# Add a subject
@login_required
def groupsubjectsadd(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Add A Subject'
    # initialize the form
    subjectsform = GroupSubjectsForm(theschool=theschool, thegroup=thegroup, thestate='Add',thesubject=None)

    # Set form action
    subjectsform.helper.form_action = reverse('addgroupsubject', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        subjectsform = GroupSubjectsForm(request.POST, theschool=theschool, thegroup=thegroup, thestate='Add',thesubject=None)
        if subjectsform.is_valid():
            # Save the subject
            thegrpsubject = subjectsform.save(commit=False)
            thegrpsubject.group = thegroup
            thegrpsubject.save()
            messages.success(request, "You successfully added a subject")
            gottourl = reverse("groupsubjectsview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":subjectsform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Edit a subject
@login_required
def groupsubjectsedit(request, randomid, groupslug, subjectslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Subject'
    # Check if a subject exists
    thesubject = get_object_or_404(Groupsubjects, group__id=thegroup.id, subject__slug=subjectslug)
    # initialize the form
    # Store initial data
    update_initial = {}
    update_initial['subject'] = thesubject.subject
    # initialize the form
    subjectsform = GroupSubjectsForm(theschool=theschool, thegroup=thegroup, thestate='Edit',thesubject=thesubject.subject, data=update_initial)

    # Set form action
    subjectsform.helper.form_action = reverse('editgroupsubject', kwargs={"randomid":randomid, "groupslug":groupslug, "subjectslug":subjectslug})

    if request.method == 'POST':
        subjectsform = GroupSubjectsForm(request.POST,theschool=theschool, thegroup=thegroup, thestate='Edit',thesubject=thesubject.subject)
        if subjectsform.is_valid():
            # Save the subject
            thesubject.subject = subjectsform.cleaned_data['subject']
            thesubject.save()
            messages.success(request, "You successfully edited a subject")
            gottourl = reverse("groupsubjectsview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":subjectsform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Delete a group subject
@login_required
def groupsubjectsdelete(request, randomid, groupslug, subjectslug):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Check if a group subject exists
    thesubject = get_object_or_404(Groupsubjects, group__id=thegroup.id, subject__slug=subjectslug)
    thesubject.delete()
    gottourl = reverse("groupsubjectsview", kwargs={"randomid":randomid, "groupslug":groupslug})
    messages.success(request, "You successfully deleted a subject")
    return redirect(gottourl)

# Show all lessons by group
@login_required
def lessonsview(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Show the lessons
    lessons = Groupsubjectteachers.objects.filter(groupsubjects__group__id=thegroup.id)
    return render(request, "frontend/groups/lessonsview.html", {"theschool":theschool, "thegroup":thegroup, "lessons":lessons})

# Add a lessons
@login_required
def lessonsadd(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Add A Lesson'
    # initialize the form
    lessonsform = LessonForm(theschool=theschool, thegroup=thegroup, thestate='Add',thelesson=None)

    # Set form action
    lessonsform.helper.form_action = reverse('addlesson', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        lessonsform = LessonForm(request.POST, theschool=theschool, thegroup=thegroup, thestate='Add',thelesson=None)
        if lessonsform.is_valid():
            # Save the lesson
            lessonsform.save()
            messages.success(request, "You successfully added a lesson")
            gottourl = reverse("lessonsview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":lessonsform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Edit a lessons
@login_required
def lessonsedit(request, randomid, groupslug, lessonid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Lesson'
    # Check if a lesson exists
    thelesson = get_object_or_404(Groupsubjectteachers, id=lessonid)
    # initialize the form
    # Store initial data
    update_initial = {}
    update_initial['groupsubjects'] = thelesson.groupsubjects
    update_initial['theclass'] = thelesson.theclass
    update_initial['teacher'] = thelesson.teacher
    update_initial['nooflessonsperweek'] = thelesson.nooflessonsperweek
    # initialize the form
    lessonsform = LessonForm(theschool=theschool, thegroup=thegroup, thestate='Edit',thelesson=thelesson, data=update_initial)

    # Set form action
    lessonsform.helper.form_action = reverse('editlesson', kwargs={"randomid":randomid, "groupslug":groupslug, "lessonid":lessonid})

    if request.method == 'POST':
        lessonsform = LessonForm(request.POST, theschool=theschool, thegroup=thegroup, thestate='Edit',thelesson=thelesson)
        if lessonsform.is_valid():
            # Save the lesson
            thelesson.groupsubjects = lessonsform.cleaned_data['groupsubjects']
            thelesson.theclass =  lessonsform.cleaned_data['theclass']
            thelesson.teacher = lessonsform.cleaned_data['teacher']
            thelesson.nooflessonsperweek = lessonsform.cleaned_data['nooflessonsperweek']
            thelesson.save()
            messages.success(request, "You successfully edited a lesson")
            gottourl = reverse("lessonsview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":lessonsform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Delete a lesson
@login_required
def lessonsdelete(request, randomid, groupslug, lessonid):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Check if a lesson exists
    thelesson = get_object_or_404(Groupsubjectteachers, id=lessonid)
    thelesson.delete()
    gottourl = reverse("lessonsview", kwargs={"randomid":randomid, "groupslug":groupslug})
    messages.success(request, "You successfully deleted a lesson")
    return redirect(gottourl)

# Show all specifications by group
@login_required
def specificationsview(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Show the specifications
    specifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=thegroup.id)
    return render(request, "frontend/groups/specificationsview.html", {"theschool":theschool, "thegroup":thegroup, "specifications":specifications})

# Add a specifications
@login_required
def specificationsadd(request, randomid, groupslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Add A Specification'
    # initialize the form
    specificationsform = GroupSpecifictionForm(thegroup=thegroup, thestate='Add',thespecification=None)

    # Set form action
    specificationsform.helper.form_action = reverse('addspecification', kwargs={"randomid":randomid, "groupslug":groupslug})

    if request.method == 'POST':
        specificationsform = GroupSpecifictionForm(request.POST, thegroup=thegroup, thestate='Add',thespecification=None)
        if specificationsform.is_valid():
            # Save the specifications
            specificationsform.save()
            messages.success(request, "You successfully added a specification")
            gottourl = reverse("specificationsview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":specificationsform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Edit a Specification
@login_required
def specificationsedit(request, randomid, groupslug, specificid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    thegroup = get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Store title of page
    thelabel = 'Edit A Specification'
    # Check if a specification exists
    thespecification = get_object_or_404(GroupSpecifiction, id=specificid)
    # initialize the form
    # Store initial data
    update_initial = {}
    update_initial['groupsubjectteachers'] = thespecification.groupsubjectteachers
    update_initial['day'] = thespecification.day
    update_initial['starttime'] = thespecification.starttime
    update_initial['endtime'] = thespecification.endtime
    # initialize the form
    specificationsform = GroupSpecifictionForm(thegroup=thegroup, thestate='Edit',thespecification=thespecification, data=update_initial)

    # Set form action
    specificationsform.helper.form_action = reverse('editspecification', kwargs={"randomid":randomid, "groupslug":groupslug, "specificid":specificid})

    if request.method == 'POST':
        specificationsform = GroupSpecifictionForm(request.POST, thegroup=thegroup, thestate='Edit',thespecification=thespecification)
        if specificationsform.is_valid():
            # Save the lesson
            thespecification.groupsubjectteachers = specificationsform.cleaned_data['groupsubjectteachers']
            thespecification.day =  specificationsform.cleaned_data['day']
            thespecification.starttime = specificationsform.cleaned_data['starttime']
            thespecification.endtime = specificationsform.cleaned_data['endtime']
            thespecification.save()
            messages.success(request, "You successfully edited a specification")
            gottourl = reverse("specificationsview", kwargs={"randomid":randomid, "groupslug":groupslug})
            return redirect(gottourl)
    return render(request, "frontend/groups/groupforms.html", {"form":specificationsform, "theschool":theschool,"thelabel":thelabel, "thegroup":thegroup})

# Delete a specification
@login_required
def specificationsdelete(request, randomid, groupslug, specificid):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the group exists
    get_object_or_404(SchoolGroups, school__randomid=randomid, slug=groupslug)
    # Check if a lesson exists
    thespecification = get_object_or_404(GroupSpecifiction, id=specificid)
    thespecification.delete()
    gottourl = reverse("specificationsview", kwargs={"randomid":randomid, "groupslug":groupslug})
    messages.success(request, "You successfully deleted a specification")
    return redirect(gottourl)