from dataclasses import fields
from pyexpat import model
from django import forms

from school.models import Streams, Subjects, Teachers
from .models import SchoolGroups, Groupbreaks, Groupclasses, Grouproutine, Groupsubjects, GroupSpecifiction, Groupsubjectteachers
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.conf import settings
from django.utils.text import slugify

# Form for adding or editing the SchooolGroups model. Ensures group name is unique per school.
class GroupsForm(forms.ModelForm):
    groupname = forms.CharField(
        required=True,
        label='Enter your Group Name',
        help_text='Should be unique per group',
    )

    lessonduration = forms.IntegerField(
        required=True,
        min_value=1,
        label='Enter Lesson Duration(In Minutes)'
    )

    class Meta:
        model = SchoolGroups
        fields = ['groupname', 'lessonduration']

    def __init__(self, *args, **kwargs):
        self.currentschool = kwargs.pop('theschool')
        self.currentstate = kwargs.pop('thestate')
        self.initialgroupname = kwargs.pop('groupname')
        super(GroupsForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super(GroupsForm, self).clean()
        enteredgroupname = cleaned_data.get("groupname")
        slugifiedtitle = slugify(enteredgroupname)

        # Get number of items matching slug groups name of current school
        checksgroupname = SchoolGroups.objects.filter(school__id=self.currentschool.id, slug=slugifiedtitle).count()

        # In case one is adding a group
        if self.currentstate == 'Add':
            if checksgroupname > 0:
                raise forms.ValidationError("The group name should be unique")
        # In case one is editing a group
        else:
            # Check if the entered name matches the initial one
            if enteredgroupname != self.initialgroupname:
                if checksgroupname > 0:
                    raise forms.ValidationError("The group name should be unique")

# Form for adding or editing Groupclasses model. Ensures a class and stream are unique per group. Ensure a class teacher is unique per class in one group.
class ClassForm(forms.ModelForm):
    classname = forms.CharField(
        required=True,
        label='Enter your class name'
    )

    class Meta:
        model = Groupclasses
        fields = ['stream', 'classteacher', 'classname']

    def __init__(self, *args, **kwargs):
        self.currentschool = kwargs.pop('theschool')
        self.currentgroup = kwargs.pop('thegroup')
        self.currentstate = kwargs.pop('thestate')
        self.initialclassname = kwargs.pop('classname')
        self.initialclassteacher = kwargs.pop('theclassteacher')
        self.initialstream = kwargs.pop('stream')


        super(ClassForm, self).__init__(*args, **kwargs)

        # Initialize teacher
        self.fields['classteacher'] = forms.ModelChoiceField(
                required=True,
                label='Choose your class teacher',
                help_text='A class teacher is unique per class',
                queryset=Teachers.objects.filter(school__id=self.currentschool.id),
            )
        
        # Initialize streams
        self.fields['stream'] = forms.ModelChoiceField(
                required=True,
                label='Choose your Stream',
                queryset=Streams.objects.filter(school__id=self.currentschool.id),
            )

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))


    def clean(self):
        cleaned_data = super(ClassForm, self).clean()
        enteredclassname = cleaned_data.get("classname")
        enteredstream = cleaned_data.get("stream")
        enteredteacher = cleaned_data.get("classteacher")
        slugifiedclass = slugify(enteredclassname + enteredstream.streamname)

        # Get number of items matching class name and stream name of current group
        checksclass = Groupclasses.objects.filter(group__id=self.currentgroup.id, slug=slugifiedclass).count()

        # Get classes with this teacher
        checkteacher = Groupclasses.objects.filter(classteacher=enteredteacher).count()

        # In case one is adding a class
        if self.currentstate == 'Add':
            if checksclass > 0:
                raise forms.ValidationError("The class name with stream name should be unique")

            # If class where the entered teacher is already a class teacher
            if checkteacher > 0:
                raise forms.ValidationError("The chosen teacher is a teacher in a different class.")
        # In case one is editing a group
        else:
            # Check if the entered name and stream matches the initial ones
            if (enteredclassname != self.initialclassname) and (enteredstream.streamname != self.initialstream):
                if checksclass > 0:
                    raise forms.ValidationError("The class name with stream name should be unique")

            if (self.initialclassteacher != enteredteacher):
                # If class where the entered teacher is already a class teacher
                if checkteacher > 0:
                    raise forms.ValidationError("The chosen teacher is a teacher in a different class.")

# Form for adding or editing Grouproutine model. Ensure the day entered is unique per group. Ensure the end time entered is greater than the start time entered.
class RoutineForm(forms.ModelForm):
    day = forms.ChoiceField(
        required=True,
        label='Choose the day',
        help_text='The day\'s value is unique in this group',
        choices=settings.DAYS,
    )
    starttime = forms.TimeField(
        required=True,
        label='Enter the start time of the this day',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'required':'required',
                'value':settings.DEFAULT_ROUTINE_START_TIME,
            }
        ),
    )
    endtime = forms.TimeField(
        required=True,
        label='Enter the end time of the this day',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'required':'required',
                'value':settings.DEFAULT_ROUTINE_END_TIME,
            }
        ),
    )

    class Meta:
        model = Grouproutine
        fields = ['day', 'starttime', 'endtime']

    def __init__(self, *args, **kwargs):
        self.currentgroup = kwargs.pop('thegroup')
        self.currentstate = kwargs.pop('thestate')
        self.initialday = kwargs.pop('initialday')
        super(RoutineForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super(RoutineForm, self).clean()
        starttime = cleaned_data.get("starttime")
        endtime = cleaned_data.get("endtime")
        enteredday = cleaned_data.get("day")

        if starttime >= endtime:
            raise forms.ValidationError("The start time should be less and not equal to the endtime") 

        # Check if there is such a day in the group
        checkday = Grouproutine.objects.filter(group__id=self.currentgroup.id, day=enteredday).count()

        # In case one is adding a routine
        if self.currentstate == 'Add':
            # If there is a match
            if checkday > 0:
                raise forms.ValidationError("You have already specified the routine of this day")
        # In case one is editing a routine
        else:
            # Check if the entered day matches the initial ones
            if (self.initialday != enteredday):
                # If there is a match
                if checkday > 0:
                    raise forms.ValidationError("You have already specified the routine of this day")

# Form for adding or editing Groupbreaks model. Ensure the day entered is present in the group's routine. Ensure the end time entered is greater than the start time entered. Ensure there is no lesson specification/break in the entered period.
class BreaksForm(forms.ModelForm):
    breakname = forms.CharField(
        required=True,
        label='Enter the Break Name',
    )

    day = forms.ChoiceField(
        required=True,
        label='Choose the day',
        choices=settings.DAYS,
    )
    starttime = forms.TimeField(
        required=True,
        label='Enter the start time of the this break',
        help_text='You must have specified routine for this day before setting a break. The end of one session/break is the start of another.',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'required':'required',
                'value':'09:10',
            }
        ),
    )
    endtime = forms.TimeField(
        required=True,
        label='Enter the end time of the this break',
        help_text='You must have specified routine for this day before setting a break.',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'required':'required',
                'value':'09:40',
            }
        ),
    )

    class Meta:
        model = Groupbreaks
        fields = ['breakname', 'day', 'starttime', 'endtime']

    def __init__(self, *args, **kwargs):
        self.currentgroup = kwargs.pop('thegroup')
        self.currentstate = kwargs.pop('thestate')
        self.initialbreak = kwargs.pop('initialbreak')
        super(BreaksForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super(BreaksForm, self).clean()
        starttime = cleaned_data.get("starttime")
        endtime = cleaned_data.get("endtime")
        theday = cleaned_data.get("day")

        if starttime >= endtime:
            raise forms.ValidationError("The start time should be less and not equal to the endtime")

        # Check if the day is in routine
        checkroutine = Grouproutine.objects.filter(group__id=self.currentgroup.id, day=theday).count()

        # If the day does not exist
        if checkroutine == 0:
            raise forms.ValidationError("The day you have chosen does not exist in the group routine")
        # If the day exists
        else:
            theroutine = Grouproutine.objects.get(group__id=self.currentgroup.id, day=theday)
            theroutine_starttime = theroutine.starttime
            theroutine_endtime = theroutine.endtime

            # Check if the break is in the range of routine
            # If the break is not in the routine range
            if (starttime < theroutine_starttime) or (endtime > theroutine_endtime):
                raise forms.ValidationError("The entered range is not within the range you entered for this day\'s routine")
            # If the break is in the routine range
            else:
                allbreaks = Groupbreaks.objects.filter(group__id=self.currentgroup.id, day=theday)
                # Confirm if there is a specification in this range
                allspecifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=self.currentgroup.id, day=theday)

                # In case one is performing an edit
                if self.currentstate == 'Edit':
                    # Perform validation unless initial values change
                    if (starttime != self.initialbreak.starttime) or (endtime != self.initialbreak.endtime) or (theday != self.initialbreak.day):
                        # Check if there is a break in this period
                        for one in allbreaks:
                            if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime <  one.endtime)):
                                raise forms.ValidationError("There is already a break in this given period")
                        
                        # Check if there is a specification during this break period
                        for one in allspecifications:
                            if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime <  one.endtime)):
                                raise forms.ValidationError("There is already a specification in this given period")
                else:
                    # Check if there is a break in this period
                    for one in allbreaks:
                        if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime <  one.endtime)):
                            raise forms.ValidationError("There is already a break in this given period")

                    # Check if there is a specification during this break period
                    for one in allspecifications:
                        if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime <  one.endtime)):
                            raise forms.ValidationError("There is already a specification in this given period")

# Form for adding or editing Groupsubjects model. Ensure you the subject entered is unique in the group. Load subjets from the subjects saved in the current school.
class GroupSubjectsForm(forms.ModelForm):

    class Meta:
        model = Groupsubjects
        fields = ['subject']

    def __init__(self, *args, **kwargs):
        self.currentschool = kwargs.pop('theschool')
        self.currentgroup = kwargs.pop('thegroup')
        self.currentstate = kwargs.pop('thestate')
        self.initialsubject = kwargs.pop('thesubject')
        super(GroupSubjectsForm, self).__init__(*args, **kwargs)

        self.fields['subject'] = forms.ModelChoiceField(
            required=True,
            label='Choose your subject',
            help_text='Subjects are chosen from the subjects entered in your school',
            queryset=Subjects.objects.filter(school__id=self.currentschool.id),
        )

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super(GroupSubjectsForm, self).clean()
        enteredsubject = cleaned_data.get("subject")

        # Get number of items matching subject in curret group
        checksubjectname = Groupsubjects.objects.filter(group__id=self.currentgroup.id, subject=enteredsubject).count()

        # In case one is adding a subject
        if self.currentstate == 'Add':
            if checksubjectname > 0:
                raise forms.ValidationError("The subject name should be unique per group")
        # In case one is editing a subject
        else:
            # Check if the entered name matches the initial one
            if enteredsubject != self.initialsubject:
                if checksubjectname > 0:
                    raise forms.ValidationError("The subject name should be unique per group")


# Form for adding or editing Groupsubjectteachers model. Load subjects of this group from groupsubjects model of current group. Load classes of current group from Groupclasses model. Load teachers from teachers saved of the current school. For a lesson, a particular class and a particular subject has only one teacher.
class LessonForm(forms.ModelForm):
    
    nooflessonsperweek = forms.IntegerField(
        required=True,
        min_value=1,
        label='Enter the number of lessons to have per week',
    )

    class Meta:
        model = Groupsubjectteachers
        fields = ['groupsubjects', 'theclass', 'teacher', 'nooflessonsperweek']

    def __init__(self, *args, **kwargs):
        self.currentschool = kwargs.pop('theschool')
        self.currentgroup = kwargs.pop('thegroup')
        self.initiallesson = kwargs.pop('thelesson')
        self.currentstate = kwargs.pop('thestate')
        super(LessonForm, self).__init__(*args, **kwargs)

        self.fields['groupsubjects'] = forms.ModelChoiceField(
            required=True,
            label='Choose your subject',
            help_text='Subjects are chosen from the subjects entered in your school',
            queryset=Groupsubjects.objects.filter(group__id=self.currentgroup.id),
        )

        self.fields['theclass'] = forms.ModelChoiceField(
            required=True,
            label='Choose the class',
            queryset=Groupclasses.objects.filter(group__id=self.currentgroup.id),
        )

        self.fields['teacher'] = forms.ModelChoiceField(
            required=True,
            label='Choose the teacher',
            queryset=Teachers.objects.filter(school__id=self.currentschool.id),
        )

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super(LessonForm, self).clean()
        groupsubjects = cleaned_data.get("groupsubjects")
        theclass = cleaned_data.get("theclass")

        # Check if lesson is present
        checklesson = Groupsubjectteachers.objects.filter(groupsubjects=groupsubjects,theclass=theclass).count()

        # In case one is adding a lesson
        if self.currentstate == 'Add':
            if checklesson > 0:
                raise forms.ValidationError("The lesson already exists")
        # In case one is editing a lesson
        else:
            # Check if the entered details matches the initial ones
            if (groupsubjects != self.initiallesson.groupsubjects) and (theclass != self.initiallesson.theclass):
                if checklesson > 0:
                    raise forms.ValidationError("The lesson already exists")

# Form for adding or editing GroupSpecification model. Load lessons of the current group. Ensure the entered period is unique. Ensure the chosen day is within the groups routine.
class GroupSpecifictionForm(forms.ModelForm):

    day = forms.ChoiceField(
        required=True,
        label='Choose the day',
        choices=settings.DAYS,
    )
    starttime = forms.TimeField(
        required=True,
        label='Enter the start time of the this lesson',
        help_text='The end of one session/break is the start of another.',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'required':'required',
            }
        ),
    )
    endtime = forms.TimeField(
        required=True,
        label='Enter the end time of the this lesson',
        widget=forms.TimeInput(
            attrs={
                'type': 'time',
                'required':'required',
            }
        ),
    )

    class Meta:
        model = GroupSpecifiction
        fields = ['groupsubjectteachers', 'day', 'starttime', 'endtime']

    def __init__(self, *args, **kwargs):
        self.currentgroup = kwargs.pop('thegroup')
        self.currentstate = kwargs.pop('thestate')
        self.initialspecification = kwargs.pop('thespecification')
        super(GroupSpecifictionForm, self).__init__(*args, **kwargs)

        self.fields['groupsubjectteachers'] = forms.ModelChoiceField(
            required=True,
            label='Choose the lesson',
            queryset=Groupsubjectteachers.objects.filter(groupsubjects__group__id=self.currentgroup.id),
        )

        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super(GroupSpecifictionForm, self).clean()
        chosenlesson = cleaned_data.get("groupsubjectteachers")
        chosenday = cleaned_data.get("day")
        starttime = cleaned_data.get("starttime")
        endtime = cleaned_data.get("endtime")

        if starttime >= endtime:
            raise forms.ValidationError("The start time should be less and not equal to the endtime") 

        # Check if specification is present
        checklesson = GroupSpecifiction.objects.filter(groupsubjectteachers=chosenlesson,day=chosenday, starttime=starttime, endtime=endtime).count()

        # In case one is adding a specification
        if self.currentstate == 'Add':
            if checklesson > 0:
                raise forms.ValidationError("The specification already exists")
        # In case one is editing a lesson
        else:
            # Check if the entered details matches the initial ones
            if (chosenlesson != self.initialspecification.groupsubjectteachers) and (chosenday != self.initialspecification.day) and (starttime != self.initialspecification.starttime) and (endtime != self.initialspecification.endtime):
                if checklesson > 0:
                    raise forms.ValidationError("The specification already exists")
        
         # Check if the day is in routine
        checkroutine = Grouproutine.objects.filter(group__id=self.currentgroup.id, day=chosenday).count()

        # If the day does not exist
        if checkroutine == 0:
            raise forms.ValidationError("The day you have chosen does not exist in the group routine")
        # If the day exists
        else:
            theroutine = Grouproutine.objects.get(group__id=self.currentgroup.id, day=chosenday)
            theroutine_starttime = theroutine.starttime
            theroutine_endtime = theroutine.endtime

            # Check if the specification is in the range of routine
            # If the specification is not in the routine range
            if (starttime < theroutine_starttime) or (endtime > theroutine_endtime):
                raise forms.ValidationError("The entered range is not within the range you entered for this day\'s routine")
            # If the break is in the routine range
            else:
                # Perform validation only if initial data changes
                if self.currentstate == 'Edit':
                    if (chosenlesson != self.initialspecification.groupsubjectteachers) and (chosenday != self.initialspecification.day) and (starttime != self.initialspecification.starttime) and (endtime != self.initialspecification.endtime):
                        # Confrim with breaks
                        allbreaks = Groupbreaks.objects.filter(group__id=self.currentgroup.id, day=chosenday)

                        for one in allbreaks:
                            if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime <  one.endtime)):
                                raise forms.ValidationError("There is already a break in this given period")

                        # Confirm if there is a specification in this range
                        allspecifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=self.currentgroup.id, day=chosenday)

                        for one in allspecifications:
                            if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime < one.endtime)):
                                raise forms.ValidationError("There is already a specification in this given period")
                else:
                    allbreaks = Groupbreaks.objects.filter(group__id=self.currentgroup.id, day=chosenday)

                    for one in allbreaks:
                        if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime < one.endtime)):
                            raise forms.ValidationError("There is already a break in this given period")

                    # Confirm if there is a specification in this range
                    allspecifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=self.currentgroup.id, day=chosenday)

                    for one in allspecifications:
                        if ((starttime <= one.starttime) and (endtime > one.starttime)) or ((starttime >= one.starttime) and (starttime < one.endtime)):
                            raise forms.ValidationError("There is already a specification in this given period")