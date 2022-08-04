from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from school.models import School
from groups.models import Groupclasses
from .models import Timetablegroup, Timetablebreaks, Timetablelessons
from .timetable import checktimetablerequiremnets_group, checktimetablerequiremnets_school, checktimetablerequiremnets, createtimetable, arrangetimetable
from .forms import TimetableGroupForm

from django.http import HttpResponse
from .pdf import html_to_pdf 
from django.template.loader import render_to_string

from timetablegenerator.settings import BASE_DIR

# Show all timetables 
@login_required
def timetablesview(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
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
    timetables = Timetablegroup.objects.filter(school__randomid=randomid)
    return render(request, "frontend/school/timetablesview.html", {"theschool":theschool,"timetables":timetables, "list_of_errors":list_of_errors, "result":result})

# Edit timetable group name
@login_required
def edittimetable(request, randomid, timetableid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the timetable group exists
    thetimetable = get_object_or_404(Timetablegroup, school__id=theschool.id, id=timetableid)
    # Store title of page
    thelabel = 'Edit Timetable Group Name'
    # initialize the form
    # Store current information in DB
    update_initial = {}
    update_initial["timetablegroupname"] = thetimetable.timetablegroupname
    timetableform = TimetableGroupForm(theschool=theschool, initialname=thetimetable.timetablegroupname, data=update_initial)

    # Set form action
    timetableform.helper.form_action = reverse('edittimetable', kwargs={"randomid":randomid, "timetableid":timetableid})

    if request.method == 'POST':
        timetableform = TimetableGroupForm(request.POST, theschool=theschool, initialname=thetimetable.timetablegroupname)
        if timetableform.is_valid():
            # Save the timetable
            thetimetable.timetablegroupname = timetableform.cleaned_data['timetablegroupname']
            thetimetable.save()
            messages.success(request, "You successfully edited a timetable")
            gotourl = reverse("timetablesview", kwargs={"randomid":randomid})
            return redirect(gotourl)
    return render(request, "frontend/school/schoolforms.html", {"form":timetableform, "theschool":theschool, "thelabel":thelabel})

# Delete timetable group
@login_required
def deletetimetable(request, randomid, timetableid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the timetable group exists
    thetimetable = get_object_or_404(Timetablegroup, school__id=theschool.id, id=timetableid)
    thetimetable.delete()
    messages.success(request, "You successfully deleted a timetable")
    gotourl = reverse("schoolview", kwargs={"randomid":randomid})
    return redirect(gotourl)

# Perform a check if can generate a timetable
@login_required
def timetablecheck(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)

    no_of_errors = checktimetablerequiremnets_school(theschool)
    # If there are erros, it is not an empty list
    if len(no_of_errors) == 0:
        # proceed to check for a each group
        no_of_errors_group = checktimetablerequiremnets_group(theschool)
        # If there are erros, it is not an empty list
        if len(no_of_errors_group) == 0:
            # Store result if checking
            theresult = True
            list_of_errors = None
        # Show errors in template
        else:
            # Store result if checking
            theresult = False
            list_of_errors = no_of_errors_group
    # Show errors in template if there are there
    else:
        # Store result if checking
        theresult = False
        list_of_errors = no_of_errors

    # If the above errors are not present
    if theresult == True:
        result = checktimetablerequiremnets(theschool)

        # If there are no errors
        if (len(result)) == 0:
            messages.success(request, "You meet all requirements to generate a timetable")
            gotourl = reverse("schoolview", kwargs={"randomid":randomid})
            return redirect(gotourl)
        # If there are errors
        else:
            # Show all errors
            return render(request, "frontend/timetables/timetablesfeedback.html", {"theschool":theschool,"results":result})
    # If the errors are present
    else:
        # Show all errors first before checking the timetable
        messages.success(request, "You must meet these requirements before checking if you meet requirements for generating a timetable")
        return render(request, "frontend/timetables/timetablesfeedback.html", {"theschool":theschool,"results":list_of_errors})

# Generate a timetable
@login_required
def generatetimetable(request, randomid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)

    no_of_errors = checktimetablerequiremnets_school(theschool)
    # If there are erros, it is not an empty list
    if len(no_of_errors) == 0:
        # proceed to check for a each group
        no_of_errors_group = checktimetablerequiremnets_group(theschool)
        # If there are erros, it is not an empty list
        if len(no_of_errors_group) == 0:
            # Store result if checking
            theresult = True
            list_of_errors = None
        # Show errors in template
        else:
            # Store result if checking
            theresult = False
            list_of_errors = no_of_errors_group
    # Show errors in template if there are there
    else:
        # Store result if checking
        theresult = False
        list_of_errors = no_of_errors


    result = checktimetablerequiremnets(theschool)

    # If the above errors are not present
    if theresult:
        # If there are no errors..Perform a generation
        if (len(result)) == 0:
            # Store the number of tries on regenerating the timetable
            tries_timetable = 1
            generate_result = createtimetable(theschool, tries_timetable)
            
            # Check if the return value is True
            if generate_result == True:
                messages.success(request, "You sucessfully generated a timetable")
                gotourl = reverse("schoolview", kwargs={"randomid":randomid})
                return redirect(gotourl)
            # If there is an error
            else:
                timetable_errors = []
                error_dict = {  
                    "error": f'There was an error creating the timetable. Please ensure the number of lessons per week are of good estimates.',
                }
                timetable_errors.append(error_dict)
                messages.success(request, "There is an error during timetable generation")
                return render(request, "frontend/timetables/timetablesfeedback.html", {"theschool":theschool,"results":timetable_errors})
        # If there are errors
        else:
            # Show all errors
            messages.success(request, "You must meet all requirements before generating a timetable")
            return render(request, "frontend/timetables/timetablesfeedback.html", {"theschool":theschool,"results":result})
    # If the errors are present
    else:
        # Show all errors first before checking the timetable
        messages.success(request, "You must meet these requirements before generating a timetable")
        return render(request, "frontend/timetables/timetablesfeedback.html", {"theschool":theschool,"results":list_of_errors})

# Show classes for this timetable group with links to view the timetable
@login_required
def timetablesingroup(request, randomid, timetableid):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the timetable group exists
    thetimetable = get_object_or_404(Timetablegroup, school__id=theschool.id, id=timetableid)

    # Get lessons and breaks with distinct classes
    class_for_lessons = Timetablelessons.objects.filter(timetablegroup__id=thetimetable.id)
    class_for_breaks = Timetablebreaks.objects.filter(timetablegroup__id=thetimetable.id)

    # Store the classes ids
    differentclasses = []

    # Add all the classes
    for one in class_for_lessons:
        the_class = one.theclass
        if the_class not in differentclasses:
            differentclasses.append(one.theclass)

    # Check if a class was in Timetable lessons but not in breaks
    for on in class_for_breaks:
        classid = on.theclass
        if classid not in differentclasses:
            differentclasses.append(classid)

    return render(request, "frontend/timetables/timetablesingroup.html", {"allclasses":differentclasses, "theschool":theschool, "thetimetable":thetimetable})

# View timetables in this timetable group
@login_required
def onetimetable(request, randomid, timetableid, classlug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the timetable group exists
    thetimetable = get_object_or_404(Timetablegroup, school__id=theschool.id, id=timetableid)
    # Get the class
    theclass = get_object_or_404(Groupclasses, group__school__id=theschool.id, slug=classlug)

    arranged_one = arrangetimetable(thetimetable, theclass)

    return render(request, "frontend/timetables/classtimetable.html", {"timetable":arranged_one, "theclass":theclass, "theschool":theschool, "thetimetable":thetimetable})

def pdftimetable(request, randomid, timetableid, classlug):
    # Check if the school exists
    theschool = get_object_or_404(School, randomid=randomid)
    # Check if the timetable group exists
    thetimetable = get_object_or_404(Timetablegroup, school__id=theschool.id, id=timetableid)
    # Get the class
    theclass = get_object_or_404(Groupclasses, group__school__id=theschool.id, slug=classlug)

    arannged_one = arrangetimetable(thetimetable, theclass)

    open(BASE_DIR / 'timetable/templates/temp.html', "w").write(render_to_string("frontend/timetables/pdfclasstimetable.html", {"timetable":arannged_one, "theschool":theschool, "theclass":theclass}))

    # Convert html template to pdf
    # Converting the HTML template into a PDF file
    pdf = html_to_pdf('temp.html')
        
    # rendering the template
    return HttpResponse(pdf, content_type='application/pdf')