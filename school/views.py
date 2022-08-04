import imp
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from .forms import RegisterForm, LoginForm, EditAccountForm, ChangePasswForm, SchoolForm, StreamForm, TeachersForm, SubjectsForm, TeachersRoutineFormHelper, addteacherroutineformset, editteacherroutineformset
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib import messages
from .models import Subjects, User, School, Teachers, Streams
from groups.models import SchoolGroups
from timetable.models import Timetablegroup
from .utilities import generate_random_id, generate_random_id_forschool, generate_random_id_forteacher
from django.contrib.auth.decorators import login_required
import random
from timetable.timetable import checktimetablerequiremnets_group, checktimetablerequiremnets_school

# registration 
# If a person is logged in they should not access the registration page
@user_passes_test(lambda u: u.is_anonymous, login_url="index", redirect_field_name=None)
def register(request):
    # Store title of page
    thelabel = 'Register'
    regform = RegisterForm()
    if request.method == 'POST':
        # process the form
        regform = RegisterForm(request.POST)
        if regform.is_valid():
            # Newly created username and password
            usern = regform.cleaned_data['username']
            passwd = regform.cleaned_data['password1']
            # Create the user and log them in
            theuser = regform.save(commit=False)
            theuser.randomid = generate_random_id()
            theuser.save()
            logineduser = authenticate(request, username=usern, password=passwd)
            if logineduser is not None:
                if logineduser.is_active:
                    login(request, logineduser)
                    messages.success(request, "Successfully registred")
                    return redirect("index")
    return render(request, "frontend/web/webforms.html", {"form":regform,"thelabel":thelabel})

# login 
# If a person is logged in they should not access the login page
@user_passes_test(lambda u: u.is_anonymous, login_url="index", redirect_field_name=None)
def loginstuff(request):
    # Store title of page
    thelabel = 'Login'
    loginform = LoginForm(request)
    if request.method == 'POST':
        loginform = LoginForm(request, data=request.POST)
        if loginform.is_valid():
            # process the form
            usern = loginform.cleaned_data['username']
            paswd = loginform.cleaned_data['password']
            # Log in the user
            logineduser = authenticate(request, username=usern, password=paswd)
            if logineduser is not None:
                if logineduser.is_active:
                    login(request, logineduser)
                    messages.success(request, "Successfully logged in")
                    return redirect("index")
    return render(request, "frontend/web/webforms.html", {"form":loginform, "thelabel":thelabel})

# Log out user
@login_required
def logoutuser(request):
    # Log out the user
    logout(request)
    return redirect("login")

# Account homepage
@login_required
def mainpage(request):
    # Display three schools and links to navigate the account
    schools = School.objects.filter(user__id=request.user.id)[:3]
    return render(request, "frontend/account/index.html", {"schools":schools})

# Delete Account Of a Given User
@login_required
def deleteaccount(request, randomid):
    # Get the User
    theuser = get_object_or_404(User, randomid=randomid)
    # Delete the user permanently
    theuser.delete()
    # Log them out
    logout(request)
    messages.success(request, "You successfully deleted your account")
    return redirect("login")

# Edit Account Information
@login_required
def editaccount(request):
    # Store the title of the page
    thelabel = 'Edit Account Information'
    # update form to have iniial values of this object
    update_initial = {}
    update_initial['first_name'] = request.user.first_name
    update_initial['last_name'] = request.user.last_name
    editform = EditAccountForm(data=update_initial)
    if request.method == "POST":
        # Process the form
        editform = EditAccountForm(request.POST)
        if editform.is_valid():
            # Save the changes
            theuser = User.objects.get(randomid=request.user.randomid)
            theuser.first_name = editform.cleaned_data['first_name']
            theuser.last_name = editform.cleaned_data['last_name']
            theuser.save()
            messages.success(request, "You have successfully updated your account")
            return redirect("index")
    return render(request, "frontend/account/accountforms.html", {"form":editform,"thelabel":thelabel})

# Change password of a given user
@login_required
def changepassword(request):
    changepassform = ChangePasswForm(user=request.user)
    # Store the title of the form
    thelabel = 'Change Password'
    if request.method == 'POST':
        changepassform = ChangePasswForm(data=request.POST, user=request.user)
        if changepassform.is_valid():
            # Save the changes
            changepassform.save()
            # update the session auth hash
            update_session_auth_hash(request, changepassform.user)
            messages.success(request, "Your password has been changed successfully")
            return redirect("index")
    return render(request, "frontend/account/accountforms.html", {"form":changepassform, "thelabel":thelabel})

# Show user account
@login_required
def useraccount(request):
    # Show links to change user account  information
    return render(request, "frontend/account/useraccount.html")

# Show all schools
@login_required
def schooldisplay(request):
    # Show all schools of current user
    schools = School.objects.filter(user__randomid=request.user.randomid)
    return render(request, "frontend/account/schools.html", {"schools":schools})

# Add new school
@login_required
def addschool(request):
    thelabel = 'Add A School'
    # initialize the form
    schoolform = SchoolForm(theuser=request.user, thestate='Add', initialschool=None)

    # Set form action
    schoolform.helper.form_action = reverse('addschool')

    if request.method == 'POST':
        schoolform = SchoolForm(request.POST, request.FILES, theuser=request.user, thestate='Add', initialschool=None)
        if schoolform.is_valid():
            # Save the school
            theschool = School()
            theschool.user = request.user
            theschool.schoolname = schoolform.cleaned_data['schoolname']
            thelogo = request.FILES.get('schoollogo', False)
            # If a file was chosen
            if thelogo != False:
                theschool.schoollogo = request.FILES['schoollogo']
            # generate a randomid for the school
            theschool.randomid = generate_random_id_forschool()
            theschool.save()
            messages.success(request, "You successfully added a school")
            return redirect("schooldisplay")
    return render(request, "frontend/account/accountforms.html", {"form":schoolform, "thelabel":thelabel})

# Edit school
@login_required
def editschool(request, randomid):
    # Get the particular school
    initialschool = get_object_or_404(School, randomid=randomid)
    # Store the title of the school
    thelabel = 'Edit A School'
    # Store Initial data of the form
    update_initial = {}
    update_initial["schoolname"] = initialschool.schoolname
    # initialze the form
    schoolform = SchoolForm(theuser=request.user, thestate='Edit', initialschool=initialschool.schoolname, data=update_initial)

    # Set form action
    schoolform.helper.form_action = reverse('editschool', kwargs={'randomid':randomid})
    if request.method == 'POST':
        schoolform = SchoolForm(request.POST, request.FILES, theuser=request.user, thestate='Edit', initialschool=initialschool.schoolname)
        if schoolform.is_valid():
            initialschool.schoolname = schoolform.cleaned_data['schoolname']
            # Check if a logo was chosen
            thelogo = request.FILES.get('schoollogo', False)
            if thelogo != False:
                initialschool.schoollogo = request.FILES['schoollogo']
            else:
                initialschool.schoologo = School._meta.get_field('schoollogo').get_default()
            # Save the changes
            initialschool.save()
            messages.success(request, "You successfully edited a school")
            return redirect("schooldisplay")
    return render(request, "frontend/account/accountforms.html", {"form":schoolform, "thelabel":thelabel})

# Delete a school
@login_required
def deleteschool(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    theschool.delete()
    messages.success(request, "You successfully deleted a school")
    return redirect("schooldisplay")

# View school Information
@login_required
def schoolview(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Show school related information?9only three in number. Groups, Subjects, Streams, Teachers, Timetables
    subjects = Subjects.objects.filter(school__randomid=randomid)[:3]
    schoolgroups = SchoolGroups.objects.filter(school__randomid=randomid)[:3]
    teachers = Teachers.objects.filter(school__randomid=randomid)[:3]
    streams = Streams.objects.filter(school__randomid=randomid)[:3]
    # Check if the school meets requirements for a timetable
    no_of_errors = checktimetablerequiremnets_school(theschool)
    # If there are erros, it is not an empty list
    if len(no_of_errors) == 0:
        # proceed to check for a each group
        no_of_errors_group = checktimetablerequiremnets_group(theschool)
        # If there are erros, it is not an empty list
        if len(no_of_errors_group) == 0:
            # Store result if checking
            result = True
            list_of_errors = None
        # Show errors in template
        else:
            # Store result if checking
            result = False
            list_of_errors = no_of_errors_group
    # Show errors in template if there are there
    else:
        # Store result if checking
        result = False
        list_of_errors = no_of_errors
    timetables = Timetablegroup.objects.filter(school__randomid=randomid)[:3]
    return render(request, "frontend/school/schoolview.html", {"theschool":theschool, "subjects":subjects, "schoolgroups":schoolgroups, "teachers":teachers, "streams":streams,"timetables":timetables, "list_of_errors":list_of_errors, "result":result})

# Show all streams for a given school
@login_required
def streamsview(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Get the streams of this school
    streams = Streams.objects.filter(school__randomid=randomid)
    return render(request, "frontend/school/streamsview.html", {"streams":streams, "theschool":theschool})

# Add a stream(unique per school)
@login_required
def streamsadd(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Store title of page
    thelabel = 'Add A Stream'
    # initialize the form
    streamform = StreamForm(theschool=theschool, thestate='Add', initialstream=None)

    # Set form action
    streamform.helper.form_action = reverse('addstream', kwargs={"randomid":randomid})

    if request.method == 'POST':
        streamform = StreamForm(request.POST, theschool=theschool, thestate='Add', initialstream=None)
        if streamform.is_valid():
            # Save the stream
            thestream = streamform.save(commit=False)
            thestream.school = theschool
            thestream.save()
            messages.success(request, "You successfully added a stream")
            gotourl = reverse("streamview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":streamform, "theschool":theschool,"thelabel":thelabel})

# Edit a stream
@login_required
def streamsedit(request, randomid, streamslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the stream exists
    thestream = get_object_or_404(Streams, school__randomid=randomid, slug=streamslug)
    # Store title of page
    thelabel = 'Edit A Stream'
    # initialize the form
    # Store current information in DB
    update_initial = {}
    update_initial["streamname"] = thestream.streamname
    streamform = StreamForm(theschool=theschool, thestate='Edit', initialstream=thestream.streamname, data=update_initial)

    # Set form action
    streamform.helper.form_action = reverse('editstream', kwargs={"randomid":randomid, "streamslug":streamslug})

    if request.method == 'POST':
        streamform = StreamForm(request.POST, theschool=theschool, thestate='Edit', initialstream=thestream.streamname)
        if streamform.is_valid():
            # Save the stream
            thestream.streamname = streamform.cleaned_data['streamname']
            thestream.save()
            messages.success(request, "You successfully edited a stream")
            gotourl = reverse("streamview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":streamform, "theschool":theschool, "thelabel":thelabel})

# Delete a stream
@login_required
def streamsdelete(request, randomid, streamslug):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the stream exists
    thestream = get_object_or_404(Streams, school__randomid=randomid, slug=streamslug)
    if thestream.ifcandelete() == True:
        thestream.delete()
        messages.success(request, "You successfully deleted a stream")
    else:
        messages.success(request, "Sorry, you can not delete this stream. Delete the timetable using with classes using this stream first")
    gotourl = reverse("streamview", kwargs={"randomid":randomid})
    return redirect(gotourl)

# Show all teachers of a given school
@login_required
def teachersview(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Get the streams of this school
    teachers = Teachers.objects.filter(school__randomid=randomid)
    return render(request, "frontend/school/teachersview.html", {"teachers":teachers, "theschool":theschool})

# Add a teacher
@login_required
def teacheradd(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Store title of page
    thelabel = 'Add A Teacher'
    # initialize the form
    teacher_form = TeachersForm()
    teacherroutineform = addteacherroutineformset()
    teacher_form_helper = TeachersRoutineFormHelper()

    if request.method == 'POST':
        teacher_form = TeachersForm(request.POST)
        form_set = addteacherroutineformset(request.POST)
        # If both teachers form and teachers routine form is valid
        if teacher_form.is_valid():
            # Save the teacher
            the_new_teacher = teacher_form.save(commit=False)
            the_new_teacher.school = theschool
            the_new_teacher.randomid = generate_random_id_forteacher()
            form_set = addteacherroutineformset(request.POST, instance=the_new_teacher)
            if form_set.is_valid():
                the_new_teacher.save()
                form_set.save()
                messages.success(request, "You successfully added a teacher")
                gotourl = reverse("teacherview", kwargs={"randomid":randomid})
                return redirect(gotourl)
            else:
                # Show there is an error
                messages.success(request, "You have either specified the routine for a day more than once or for one day, the start time is greater than or equal to the endtime")
    return render(request, "frontend/school/teachersform.html", {"form":teacher_form,"formset":teacherroutineform,"formset_helper":teacher_form_helper, "theschool":theschool,"thelabel":thelabel})

# Edit a teacher
@login_required
def teacheredit(request, randomid, teacherrandomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the teacher exists
    theteacher = get_object_or_404(Teachers, school__randomid=randomid, randomid=teacherrandomid)
    # Store title of page
    thelabel = 'Edit A Teacher'
    # initialize the form
    # Store current information in DB
    update_initial = {}
    update_initial["teachername"] = theteacher.teachername
    teacherform = TeachersForm(data=update_initial)

    # teacher_form = TeachersForm()
    teacherroutineform = editteacherroutineformset(instance=theteacher)
    teacher_form_helper = TeachersRoutineFormHelper()

    if request.method == 'POST':
        teacherform = TeachersForm(request.POST)
        if teacherform.is_valid():
            # Save the teacher changes
            theteacher.teachername = teacherform.cleaned_data['teachername']
            theteacher.save()
            messages.success(request, "You successfully edited a teacher")
            gotourl = reverse("teacherview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/teacherformsedit.html", {"form":teacherform,"formset":teacherroutineform,"formset_helper":teacher_form_helper, "theschool":theschool,"thelabel":thelabel, "ateacherrandomid":teacherrandomid})

# Delete a teacher
@login_required
def teacherdelete(request, randomid, teacherrandomid):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the teacher exists
    theteacher = get_object_or_404(Teachers, school__randomid=randomid, randomid=teacherrandomid)
    if theteacher.ifcandelete() == True:
        theteacher.delete()
        messages.success(request, "You successfully deleted a teacher")
    else:
        messages.success(request, "Sorry, you can not delete this teacher. Delete the timetable using with teacher")
    gotourl = reverse("teacherview", kwargs={"randomid":randomid})
    return redirect(gotourl)

# Show all subjects
@login_required
def subjectsview(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Get the subjects of this school
    subjects = Subjects.objects.filter(school__randomid=randomid)
    return render(request, "frontend/school/subjectsview.html", {"subjects":subjects, "theschool":theschool})

# Add a subjects
@login_required
def subjectsadd(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Store title of page
    thelabel = 'Add A Subject'
    # initialize the form
    subjectform = SubjectsForm(theschool=theschool, thestate='Add', subjectname=None)

    # Set form action
    subjectform.helper.form_action = reverse('addsubject', kwargs={"randomid":randomid})

    if request.method == 'POST':
        subjectform = SubjectsForm(request.POST, theschool=theschool, thestate='Add', subjectname=None)
        if subjectform.is_valid():
            # Save the stream
            thesubject = subjectform.save(commit=False)
            # generate a random color for a subject
            # Join the random hexadacimeal digits with no space between each other to the '#' symbol
            thesubject.color = "#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])
            thesubject.school = theschool
            thesubject.save()
            messages.success(request, "You successfully added a subject")
            gotourl = reverse("subjectview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":subjectform, "theschool":theschool,"thelabel":thelabel})

# Edit a subject
@login_required
def subjectsedit(request, randomid, subjectslug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the subject exists
    thesubject = get_object_or_404(Subjects, school__randomid=randomid, slug=subjectslug)
    # Store title of page
    thelabel = 'Edit A Subject'
    # initialize the form
    # Store current information in DB
    update_initial = {}
    update_initial["subjectname"] = thesubject.subjectname
    subjectform = SubjectsForm(theschool=theschool, thestate='Edit', subjectname=thesubject.subjectname, data=update_initial)

    # Set form action
    subjectform.helper.form_action = reverse('editsubject', kwargs={"randomid":randomid, "subjectslug":subjectslug})

    if request.method == 'POST':
        subjectform = SubjectsForm(request.POST, theschool=theschool, thestate='Edit', subjectname=thesubject.subjectname)
        if subjectform.is_valid():
            # Save the subject
            thesubject.subjectname = subjectform.cleaned_data['subjectname']
            thesubject.save()
            messages.success(request, "You successfully edited a subject")
            gotourl = reverse("subjectview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":subjectform, "theschool":theschool, "thelabel":thelabel})

# Delete a subject
@login_required
def subjectsdelete(request, randomid, subjectslug):
    # Check if the school exists
    get_object_or_404(School, randomid=randomid)
    # Check if the subject exists
    thesubject = get_object_or_404(Subjects, school__randomid=randomid, slug=subjectslug)
    if thesubject.ifcandelete() == True:
        thesubject.delete()
        messages.success(request, "You successfully deleted a subject")
    else:
        messages.success(request, "Sorry, you can not delete this subject. Delete the timetable using this subject")
    gotourl = reverse("subjectview", kwargs={"randomid":randomid})
    return redirect(gotourl)