from school.models import Subjects, Teachers, Streams, TeachersRoutine
from groups.models import SchoolGroups, Groupsubjects, Groupsubjectteachers, Grouproutine, Groupclasses, GroupSpecifiction, Groupbreaks
from timetable.models import Timetablegroup, Timetablelessons, Timetablebreaks
from django.conf import settings
import random
from datetime import timedelta, time

# Check whether a particular school meets the requirements of generating a timetable(having teachers, subjects, streams, groups). It reports on any encountered errors.
def checktimetablerequiremnets_school(theschool):
    # Store all errors
    timetableerrors = []

    # Ensure the school has subjects
    checksubjects = Subjects.objects.filter(school__id=theschool.id).count()
    # If there are no subjects
    if checksubjects == 0:
        error_dict = {
            "error": 'You must have subjects in the school',
        }
        timetableerrors.append(error_dict)

    # Ensure the school has teachers
    checkteachers = Teachers.objects.filter(school__id=theschool.id).count()
    # If there are no teachers
    if checkteachers == 0:
        error_dict = {
            "error": 'You must have teachers in the school',
        }
        timetableerrors.append(error_dict)

    # Ensure the school has streasms
    checkstreams = Streams.objects.filter(school__id=theschool.id).count()
    # If there are no streams
    if checkstreams == 0:
        error_dict = {
            "error": 'You must have streams in the school',
        }
        timetableerrors.append(error_dict)

    # Ensure the school has groups
    checkgroups = SchoolGroups.objects.filter(school__id=theschool.id).count()
    # If there are no groups
    if checkgroups == 0:
        error_dict = {
            "error": 'You must have groups in the school',
        }
        timetableerrors.append(error_dict)

    return timetableerrors

# If the school meets the requirements, it checks whether the groups of a particular school haas subjects within it, classes, lessons and routines. It reports on any encountered errors.
def checktimetablerequiremnets_group(theschool):
    # Store all errors
    timetableerrors = []

    # Get the groups of the school
    schoolgrps = SchoolGroups.objects.filter(school__id=theschool.id)

    # Loop though all groups
    for agroup in schoolgrps:
        # Ensure the group has subjects
        checksubjects = Groupsubjects.objects.filter(group__id=agroup.id).count()
        # If there are no subjects
        if checksubjects == 0:
            error_dict = {
                "error": f'In Group: {agroup.groupname}, you must have subjects',
            }
            timetableerrors.append(error_dict)

        # Ensure the group has classes
        checkclasses = Groupclasses.objects.filter(group__id=agroup.id).count()
        # If there are no classes
        if checkclasses == 0:
            error_dict = {
                "error": f'In Group: {agroup.groupname}, you must have classes',
            }
            timetableerrors.append(error_dict)

        # Ensure the group has lessons
        checklessons = Groupsubjectteachers.objects.filter(groupsubjects__group__id=agroup.id).count()
        # If there are no lessons
        if checklessons == 0:
            error_dict = {
                "error": f'In Group: {agroup.groupname}, you must have lessons. Ensure you have a routine for this day, the subjects in this group and classes in this group before adding a lesson',
            }
            timetableerrors.append(error_dict)

        # Ensure the group has routine
        checkroutine = Grouproutine.objects.filter(group__id=agroup.id).count()
        # If there are no routine
        if checkroutine == 0:
            error_dict = {
                "error": f'In Group: {agroup.groupname}, you must have a routine for all days to include in your timetable.',
            }
            timetableerrors.append(error_dict)

    return timetableerrors

# Check general timetable requirements
# If there are no errors from checktimetablerequiremnets_school and checktimetablerequiremnets_group
# checks to see for all classes in the school, the given group's lesson duration, breaks, lesson specifications all lie within the routine of its group. 
# It reports on any encountered errors. 
# This function uses for four other functions which run recursively depending on whether a given group has breaks or not and if a given class has lesson specifications or not. 
# The four functions stop when the start time they are incrementing is equal to or greater than the routine end time of aa particular day. If the value is greater, an error is reported. The four functions update the start time  and the indexes of breaks or the indexes of class specifications appropriately ensuing the list does not become of ouf range.
def checktimetablerequiremnets(theschool):
    # Store all errors
    timetableerrors = []

    # Get the groups of the school
    schoolgrps = SchoolGroups.objects.filter(school__id=theschool.id)

    # Loop though all groups
    for agroup in schoolgrps:
        # Get the routine of this group
        allroutines = Grouproutine.objects.filter(group__id=agroup.id)
        # Get all classes in this group
        allclasses = Groupclasses.objects.filter(group__id=agroup.id)
        # Loop through all routines
        for aroutine in allroutines:
            # Get all breaks for this day
            allbreaks = Groupbreaks.objects.filter(group__id=agroup.id, day=aroutine.day).order_by('starttime')
            thebreakscount = allbreaks.count()
            # Loop though all classes
            for aclass in allclasses:
                # Get the lesson specifications for this class in this day
                classspecifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=agroup.id, groupsubjectteachers__theclass__id=aclass.id, day=aroutine.day).order_by('starttime')
                classspecificationscount = classspecifications.count()

                # Convert lesson duration to minutes
                lesson_duration_time = time(minute=agroup.lessonduration)

                lesson_duration = timedelta(hours=lesson_duration_time.hour, minutes=lesson_duration_time.minute, seconds=lesson_duration_time.second)
                routine_start = timedelta(hours=aroutine.starttime.hour, minutes=aroutine.starttime.minute, seconds=aroutine.starttime.second)
                routine_end = timedelta(hours=aroutine.endtime.hour, minutes=aroutine.endtime.minute, seconds=aroutine.endtime.second)

                # If there are no breaks and no specifications
                if (thebreakscount == 0) and (classspecificationscount == 0):
                    class_nospecifications_nobreaks(aclass, routine_start, routine_end, lesson_duration, timetableerrors, aroutine.day)
                # If there are no breaks but there are specifications
                elif (thebreakscount == 0) and (classspecificationscount > 0):
                    # Start specifications index at 0
                    j = 0
                    # Store if the value of specification index can change. Default is true
                    new_specific_index = True
                    class_withspecifications_nobreaks(aclass, routine_start, routine_end, classspecifications, lesson_duration, j, timetableerrors, classspecificationscount, new_specific_index, aroutine.day)
                # If there are breaks and there are specifications
                elif (thebreakscount > 0) and (classspecificationscount > 0):
                    # Start breaks index at 0
                    i = 0
                    # Start specifications index at 0
                    j = 0
                    # Store if the value of specification index can change. Default is true
                    new_specific_index = True
                    # Store if value of break index can change. Default value is true
                    new_break_index = True
                    class_withspecifications_withbreaks(aclass, routine_start, routine_end, allbreaks, classspecifications, lesson_duration, i, j, timetableerrors, thebreakscount, classspecificationscount, new_specific_index, new_break_index, aroutine.day)
                # If there are breaks but no specifications
                else:
                    # Start breaks index at 0
                    i = 0
                    # Store if value of break index can change. Default value is true
                    new_break_index = True
                    class_nopecifications_withbreaks(aclass, routine_start, routine_end, allbreaks, lesson_duration, i, timetableerrors, thebreakscount, new_break_index, aroutine.day)

    return timetableerrors

# Check time for a class with no breaks and no specifications
def class_nospecifications_nobreaks(current_class, routine_start, routine_end, lesson_duration, timetableerrors, the_day):
    thstart_time = routine_start

    # Stop recursion when the current start time matches the end time
    if (thstart_time == routine_end):
        return
    elif (thstart_time > routine_end):
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding a lesson on {the_day}. The time exceeds the end time you specified for {the_day}\'s routine. Ensure the routine\'s end time aligns with the lesson duration',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return
        
    lesson_end = thstart_time + lesson_duration
    # There is an arror
    if (lesson_end > routine_end):
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding a lesson at {thstart_time}. HINT: The duration of a lesson should align with the day\'s routine, day\'s breaks.',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return
    else:
        thstart_time += lesson_duration

    class_nospecifications_nobreaks(current_class, thstart_time, routine_end, lesson_duration, timetableerrors, the_day)

# Check time for a class with no breaks but have specifications
def class_withspecifications_nobreaks(current_class, routine_start, routine_end, allspecifications, lesson_duration, specificationsindex, timetableerrors, specificcount, new_specific_index, the_day):
    thstart_time = routine_start
    specification_torefer_to = allspecifications[specificationsindex]

    # Stop recursion when the current start time matches the end time
    if (thstart_time == routine_end):
        return
    elif (thstart_time > routine_end):
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding a lesson on {the_day}. The time exceeds the end time you specified for {the_day}\'s routine. Ensure the routine\'s end time aligns with the lesson duration',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return
    # update the start time
    # Check if the start time of the specification is a match
    specification_start_time = timedelta(hours=specification_torefer_to.starttime.hour, minutes=specification_torefer_to.starttime.minute, seconds=specification_torefer_to.starttime.second)
    if (thstart_time == specification_start_time):
        specification_end_time = timedelta(hours=specification_torefer_to.endtime.hour, minutes=specification_torefer_to.endtime.minute, seconds=specification_torefer_to.endtime.second)
        thstart_time = specification_end_time
        # update specifications index.. Only if specifications index is less than number of specifications
        newspecificindex = specificationsindex + 1
        if (newspecificindex < specificcount):
            specificationsindex += 1
        else:
            # Update this value
            new_specific_index = False
        
    # Check if the start time of routine is less than the start time of the specification I am to refer to
    elif (thstart_time < specification_start_time) or (new_specific_index == False):
        # update the start time
        thstart_time += lesson_duration

    # If the starttime is greater than the specifications's startime
    else:
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding the lesson( {specification_torefer_to.groupsubjectteachers}). HINT: The duration of a lesson should align with the day\'s routine, and day\'s specifications(if any)',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return

    class_withspecifications_nobreaks(current_class, thstart_time, routine_end, allspecifications, lesson_duration, specificationsindex, timetableerrors, specificcount, new_specific_index, the_day)

# Check time for a class with breaks and specifications
def class_withspecifications_withbreaks(current_class, routine_start, routine_end, allbreaks, allspecifications, lesson_duration, breakindex, specificationsindex, timetableerrors, breakcount, specificcount, new_specific_index, new_break_index, the_day):
    thstart_time = routine_start
    specification_torefer_to = allspecifications[specificationsindex]
    # Stop recursion when the current start time matches the end time
    if (thstart_time == routine_end):
        return
    elif (thstart_time > routine_end):
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding a lesson on {the_day}. The time exceeds the end time you specified for {the_day}\'s routine. Ensure the routine\'s end time aligns with the lesson duration',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return

    # update the start time
    # Check if the start time of the specification is a match
    specification_start_time = timedelta(hours=specification_torefer_to.starttime.hour, minutes=specification_torefer_to.starttime.minute, seconds=specification_torefer_to.starttime.second)
    if (thstart_time == specification_start_time):
        specification_end_time = timedelta(hours=specification_torefer_to.endtime.hour, minutes=specification_torefer_to.endtime.minute, seconds=specification_torefer_to.endtime.second)
        thstart_time = specification_end_time
        # update specifications index.. Only if specifications index is less than number of specifications
        newspecificindex = specificationsindex + 1
        if (newspecificindex < specificcount):
            specificationsindex += 1
            
        else:
            # Update this value
            new_specific_index = False

        class_withspecifications_withbreaks(current_class, thstart_time, routine_end, allbreaks, allspecifications, lesson_duration, breakindex, specificationsindex, timetableerrors, breakcount, specificcount, new_specific_index, new_break_index, the_day)
    # Check if the start time of routine is less than the start time of the specification I am to refer to
    elif (thstart_time < specification_start_time) or (new_specific_index == False):
        # Check with the breaks
        breaktorefer = allbreaks[breakindex]

        # If the start time matches the one for the break
        break_start_time = timedelta(hours=breaktorefer.starttime.hour, minutes=breaktorefer.starttime.minute, seconds=breaktorefer.starttime.second)
        if (thstart_time == break_start_time):
            break_end_time = timedelta(hours=breaktorefer.endtime.hour, minutes=breaktorefer.endtime.minute, seconds=breaktorefer.endtime.second)
            thstart_time = break_end_time
            # update breaks index. Only if breakindex is lesser than the number of breaks
            newbreakindex = breakindex + 1
            if (newbreakindex < breakcount):
                breakindex += 1
            else:
                # Update value
                new_break_index = False
        # If the start time is less than the break's starttime
        elif (thstart_time < break_start_time) or (new_break_index == False):
            thstart_time += lesson_duration
        # If the start time is greater than the start time of this break
        else:
            # There is an arror
            error_dict = {
                "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding a lesson on {the_day}. The time exceeds the end time you specified for {the_day}\'s routine. Ensure the routine\'s end time aligns with the lesson duration',
            }
            timetableerrors.append(error_dict)
            # Stop recursion for the current class
            return
        class_withspecifications_withbreaks(current_class, thstart_time, routine_end, allbreaks, allspecifications, lesson_duration, breakindex, specificationsindex, timetableerrors, breakcount, specificcount, new_specific_index, new_break_index, the_day)
    # If the starttime is greater than the specifications's startime
    else:
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding the lesson( {specification_torefer_to.groupsubjectteachers}). HINT: The duration of a lesson should align with the day\'s routine, day\'s breaks and day\'s specifications(if any)',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return

# Check time for a class with breaks and no specifications
def class_nopecifications_withbreaks(current_class, routine_start, routine_end, allbreaks, lesson_duration, breakindex, timetableerrors, breakcount, new_break_index, the_day):
    thstart_time = routine_start

    # Stop recursion when the current start time matches the end time
    if (thstart_time == routine_end):
        return
    elif (thstart_time > routine_end):
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding a lesson on {the_day}. The time exceeds the end time you specified for {the_day}\'s routine. Ensure the routine\'s end time aligns with the lesson duration',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return

    # Check with the breaks
    breaktorefer = allbreaks[breakindex]

    # If the start time matches the one for the break
    break_start_time = timedelta(hours=breaktorefer.starttime.hour, minutes=breaktorefer.starttime.minute, seconds=breaktorefer.starttime.second)
    if (thstart_time == break_start_time):
        break_end_time = timedelta(hours=breaktorefer.endtime.hour, minutes=breaktorefer.endtime.minute, seconds=breaktorefer.endtime.second)
        thstart_time = break_end_time
        # update breaks index. Only if breakindex is lesser than the number of breaks
        newbreakindex = breakindex + 1
        if (newbreakindex < breakcount):
            breakindex += 1
        else:
                # Update value
                new_break_index = False
    # If the start time is less than the break's starttime
    elif (thstart_time < break_start_time) or (new_break_index == False):
        thstart_time += lesson_duration
    # If the start time is greater than the start time of this break
    else:
        # There is an arror
        error_dict = {
            "error": f'For the class {current_class.classname } of the stream {current_class.stream.streamname}, there was an error when adding {breaktorefer.breakname}. HINT: The duration of a lesson should align with the day\'s routine, day\'s breaks',
        }
        timetableerrors.append(error_dict)
        # Stop recursion for the current class
        return

    class_nopecifications_withbreaks(current_class, thstart_time, routine_end, allbreaks, lesson_duration, breakindex, timetableerrors, breakcount, new_break_index, the_day)

# The calculate time function returns a date time object based on the number of seconds taken as an input
def calculate_time(seconds):
    minutes = seconds // 60
    seconds_number = seconds % 60
    hours_number = minutes // 60
    minutes_number = minutes - (hours_number * 60)
    return time(hour=hours_number, minute=minutes_number, second=seconds_number)


# Create a timetable
def createtimetable(theschool, tries_timetable):
    # Only tries to create a imetable three tines, if there is an error, it tells the user to try again.
    if (tries_timetable == 3):
        return False

    # Get number of timetables of the school
    timetable_number = Timetablegroup.objects.filter(school__id=theschool.id).count()
    # Creates a new timetablegroup with an auto generated name
    timetable_name = f'Timetable_{timetable_number+1}'
    newtimetable = Timetablegroup()
    newtimetable.school = theschool
    newtimetable.timetablegroupname = timetable_name
    newtimetable.save()

    # Store the lessons of a given day of a given teacher
    # Ensure there is no collisions occuring during the geneation of a timetable.
    teacherlessons = []
    # Get all teachers in the school
    allteachers = Teachers.objects.filter(school__id=theschool.id)
    # Loop for all teachers
    for oneteacher in allteachers:
        all_days = []
        # Loop through all days
        for x, y in settings.DAYS:
            one_day = {}
            one_day['theday'] = y
            one_day[x] = []
            all_days.append(one_day)

        name_dict = {}
        name_dict['teacherid'] = oneteacher.randomid
        name_dict['days'] = all_days

        teacherlessons.append(name_dict)

    # Get the groups of the school
    schoolgrps = SchoolGroups.objects.filter(school__id=theschool.id)

    # Loop through all specifications in the groups of a particular school and add the lessons in the list of 'teacherlessons' to ensure those sessions are booked and the teacher does not have another lesson at this particular time.
    for agroup in schoolgrps:
        # Store all group specifications
        group_specifications = GroupSpecifiction.objects.filter(groupsubjectteachers__groupsubjects__group__id=agroup.id)
        # Loop through all specifications
        for t in group_specifications:
            group_specification_start_time = timedelta(hours=t.starttime.hour, minutes=t.starttime.minute, seconds=t.starttime.second)
            group_specification_end_time = timedelta(hours=t.endtime.hour, minutes=t.endtime.minute, seconds=t.endtime.second)

            # Update the teacher with this lesson
            # Loop though all teacherlessons
            for i in range(len(teacherlessons)):
                if teacherlessons[i]['teacherid'] == t.groupsubjectteachers.teacher.randomid:
                    group_teacher_days = teacherlessons[i]['days']
                    # Get the particular day
                    for j in range(len(group_teacher_days)):
                        if (group_teacher_days[j]['theday'] == t.day):
                            group_teacher_specificday = group_teacher_days[j][t.day]

                            # Store teacher - day related info
                            teacher_dict = {}
                            teacher_dict['class'] = t.groupsubjectteachers.theclass
                            teacher_dict['start_time'] = group_specification_start_time
                            teacher_dict['end_time'] = group_specification_end_time

                            # Check if group_teacher_specificday is an empy list
                            if len(group_teacher_days) == 0:
                                # add to teacher day
                                group_teacher_specificday.append(teacher_dict)
                            # Check that there is no collission
                            else:
                                for k in range(len(group_teacher_specificday)):
                                    group_teacher_starttime = group_teacher_specificday[k]['start_time']
                                    group_teacher_endtime = group_teacher_specificday[k]['end_time']

                                    # Check if there will be a collision on adding
                                    if ((group_specification_start_time <= group_teacher_starttime) and  (group_specification_end_time > group_teacher_starttime)) or ((group_specification_start_time >= group_teacher_starttime) and (group_specification_start_time < group_teacher_endtime)):
                                        # There is an arror
                                        newly_created = Timetablegroup.objects.get(id=newtimetable.id)
                                        newly_created.delete()
                                        timetable_errors = []
                                        error_dict = {
                                            "error": f'There was an error adding the lesson specifications for teacher {one_specification.groupsubjectteachers.teacher.teachername} since he/she has another lesson at this time',
                                        }
                                        timetable_errors.append(error_dict)
                                        return timetable_errors
                                # add to teacher day
                                group_teacher_specificday.append(teacher_dict)
                    # break the loop after a match
                    break

    # Loop though all groups
    for agroup in schoolgrps:
        # Get the routine of this group
        allroutines = Grouproutine.objects.filter(group__id=agroup.id)
        # Get all classes in this group
        allclasses = Groupclasses.objects.filter(group__id=agroup.id)
        # Store the number of lessons per week of a given subject and class
        # keeps track of how many lessons of a particular class have been added until it has reached the number of lessons specified by a user. At first, all number of lessons added is initialized to zero.
        lessons_number = []
        # Get all lessons
        all_lessons = Groupsubjectteachers.objects.filter(groupsubjects__group__id=agroup.id)
        for one in all_lessons:
            my_dict = {}
            my_dict['groupsubjects'] = one.groupsubjects
            my_dict['theclass'] = one.theclass
            my_dict['teacher'] = one.teacher
            my_dict['nooflessonsperweek'] = one.nooflessonsperweek
            my_dict['current_number'] = 0
            lessons_number.append(my_dict)
            
        # Loop through all routines
        for aroutine in allroutines:
            # Get all breaks for this day
            allbreaks = Groupbreaks.objects.filter(group__id=agroup.id, day=aroutine.day).order_by('starttime')
            thebreakscount = allbreaks.count()

            # Loop though all classes
            for aclass in allclasses:
                # Check all lessons for a given class
                check_lessons = Groupsubjectteachers.objects.filter( theclass__id=aclass.id).count()
                # If there are no lessons, the program should continue until it encounters a class with a lesson specified
                if check_lessons == 0:
                    pass
                # If there are some lessons
                else:
                    # stores the lessons of a particular class
                    classlessons = []

                    # The start time to start with as one begins the timetable
                    the_start_time = timedelta(hours=aroutine.starttime.hour, minutes=aroutine.starttime.minute, seconds=aroutine.starttime.second)

                    # Check the lesson specifications for this class in this day
                    classspecifications = GroupSpecifiction.objects.filter( groupsubjectteachers__theclass__id=aclass.id, day=aroutine.day).order_by('starttime')
                    classspecificationscount = classspecifications.count()
                    
                    # If there are specifications of this current class at a particular day, add then updating them to the classlessons list and update the lesson_number list.
                    if classspecificationscount > 0:
                        # Loop through all specifications
                        for one_specification in classspecifications:
                            # Update the start time for this class if the start time and this specification start time matches
                            specification_start_time = timedelta(hours=one_specification.starttime.hour, minutes=one_specification.starttime.minute, seconds=one_specification.starttime.second)
                            specification_end_time = timedelta(hours=one_specification.endtime.hour, minutes=one_specification.endtime.minute, seconds=one_specification.endtime.second)
                            if (the_start_time == specification_start_time):
                                the_start_time = specification_end_time

                            lesson_dict = {}
                            lesson_dict['teacher'] = one_specification.groupsubjectteachers.teacher
                            lesson_dict['subject'] = one_specification.groupsubjectteachers.groupsubjects.subject
                            lesson_dict['start_time'] = specification_start_time
                            lesson_dict['end_time'] = specification_end_time

                            # Update the classlessons
                            classlessons.append(lesson_dict)

                            # Teachers are already updated so there is no need
                            
                            # lessons number
                            for alesson in lessons_number:
                                # Update where there is a match
                                if (alesson['groupsubjects'] == one_specification.groupsubjectteachers.groupsubjects) and (alesson['theclass'] == one_specification.groupsubjectteachers.theclass) and (alesson['teacher'] == one_specification.groupsubjectteachers.teacher):
                                    alesson['current_number'] += 1
                
                    # Get all subjects of this class
                    all_subjects = Groupsubjectteachers.objects.filter(theclass__id=aclass.id)

                    # Store all distinct subjects
                    all_class_subjects = []
                    for i in range(len(all_subjects)):
                        subject_name = all_subjects[i].groupsubjects.subject.subjectname
                        if subject_name not in all_class_subjects:
                            all_class_subjects.append(subject_name) 

                    # Store the break index to refer to which break
                    breakindex = 0

                    # Store if the current start time is already in the class specifications
                    matching = 0

                    # Store tries if there is issue with subject
                    # Keep track of the number of tries one has done
                    tries_subjects = 1
                    # Store tries if there is issue with teacher
                    # Keep track of the number of tries one has done
                    tries_teacher = 1
                    
                    # Do for all lessons in this day until the routine endtime
                    the_end_time = timedelta(hours=aroutine.endtime.hour, minutes=aroutine.endtime.minute, seconds=aroutine.endtime.second)

                    # Perform a loop until the updatted start time matches the end time.
                    while (the_start_time < the_end_time):
                        # Loop through all lessons already present (Specifications added earlier in the program)
                        for r in range(len(classlessons)):
                            # Check if the current start time has a period for specified already
                            if (classlessons[r]['start_time'] == the_start_time):
                                # Match to store the current index
                                matching = r
                        
                        # After finding a match
                        # If there was a match..Update the start time
                        if matching != 0:
                            # update the start time
                            the_start_time = classlessons[matching]['end_time']

                            # Update the match to zero
                            matching = 0

                        # If there was no match
                        else:
                            break_referringto = allbreaks[breakindex]

                            # If the time matches for this break
                            break_start_time = timedelta(hours=break_referringto.starttime.hour, minutes=break_referringto.starttime.minute, seconds=break_referringto.starttime.second)
                            break_end_time = timedelta(hours=break_referringto.endtime.hour, minutes=break_referringto.endtime.minute, seconds=break_referringto.endtime.second)
                            
                            # check to see if the current session aligns with a break. If so, update the start time and the break index to refer to carefully ensuring the value does not go out of range.
                            if (the_start_time == break_start_time):
                                # update the start time
                                the_start_time = break_end_time
                                # update breaks index. Only if breakindex is lesser than the number of breaks
                                newbreakindex = breakindex + 1
                                if (newbreakindex < thebreakscount):
                                    breakindex += 1

                            # If the start time does not match for the break
                            else:
                                # Store the subjects which have not been done
                                subjectstopick = all_class_subjects.copy()

                                # Pick a random subject
                                random_subject = random.choice(subjectstopick)
                                
                                # Get the lesson details on the chosen subject
                                thelesson_fromdb = Groupsubjectteachers.objects.get(groupsubjects__subject__subjectname=random_subject, groupsubjects__group__id=agroup.id, theclass__id=aclass.id)

                                current_number_lessons = 0
                                max_number_lessons = 0
                                # Check number of lessons fulfilled and maximum number
                                # use the details to compare with the lesson_number list
                                for alesson in lessons_number:
                                    # Update where there is a match
                                    if (alesson['groupsubjects'] == thelesson_fromdb.groupsubjects) and (alesson['theclass'] == thelesson_fromdb.theclass) and (alesson['teacher'] == thelesson_fromdb.teacher):
                                        current_number_lessons = alesson['current_number']
                                        max_number_lessons = alesson['nooflessonsperweek']

                                # Do for subjects which have not reached maximum  number of lessons
                                if current_number_lessons <= max_number_lessons:
                                    # Ensure it is initialized to one
                                    tries_subjects = 1
                                    # Variable to check if the teacher's routine is okay
                                    routine_check = 0

                                    # Convert lesson duration to minutes
                                    lesson_duration_time = time(minute=agroup.lessonduration)

                                    lesson_duration = timedelta(hours=lesson_duration_time.hour, minutes=lesson_duration_time.minute, seconds=lesson_duration_time.second)
                                    # Store the time the lesson is to end
                                    expected_time_tooend = the_start_time + lesson_duration

                                    # Update the teacher with this lesson
                                    # Loop though all teacherlessons
                                    for i in range(len(teacherlessons)):
                                        if teacherlessons[i]['teacherid'] == thelesson_fromdb.teacher.randomid:
                                            teacher_days = teacherlessons[i]['days']
                                            # Get the particular day
                                            for j in range(len(teacher_days)):
                                                if (teacher_days[j]['theday'] == aroutine.day):
                                                    teacher_specificday = teacher_days[j][aroutine.day]
                                                    # Check if teacher_specificday is an empy list
                                                    # Proceed to check routine if it is not an empty list
                                                    if len(teacher_days) > 0:
                                                        for k in range(len(teacher_specificday)):
                                                            teacher_starttime = teacher_specificday[k]['start_time']
                                                            teacher_endtime = teacher_specificday[k]['end_time']


                                                            # Check if there will be a collision on adding
                                                            if ((the_start_time <= teacher_starttime) and (expected_time_tooend > teacher_starttime)) or ((the_start_time >= teacher_starttime) and (the_start_time < teacher_endtime)):
                                                                # There is an arror
                                                                routine_check += 1
                                                
                                            # break the loop after a match
                                            break
                                    
                                    # Get the teachers routine
                                    teacher_routine = TeachersRoutine.objects.get(teacher__id=thelesson_fromdb.teacher.id, day=aroutine.day)

                                    # Check if it will be in teacher routine range
                                    teacher_start_time = timedelta(hours=teacher_routine.starttime.hour, minutes=teacher_routine.starttime.minute, seconds=teacher_routine.starttime.second)
                                    teacher_end_time = timedelta(hours=teacher_routine.endtime.hour, minutes=teacher_routine.endtime.minute, seconds=teacher_routine.endtime.second)
                                    if ((the_start_time < teacher_start_time) and (expected_time_tooend > teacher_end_time)):
                                        # There is an arror
                                        routine_check += 1

                                    # If there is collision with theachers routine,  the function tries again for all subjects. In case there is an issue still, the function deletes the current timetable and start the process of creating a timetable again.
                                    if routine_check != 0:
                                        # Update routine check to 0
                                        routine_check = 0
                                        # If this is the first try
                                        if tries_teacher == 1:
                                            starttimeconfirm = the_start_time
                                        
                                        if the_start_time == starttimeconfirm:
                                            tries_teacher += 1

                                        # If done this for all subjects
                                        if (tries_teacher == (len(all_class_subjects))):
                                            
                                            # Delete the timetable group
                                            newly_created = Timetablegroup.objects.get(id=newtimetable.id)
                                            newly_created.delete()
                                            tries_timetable += 1
                                            
                                            timetable_errors = []
                                            error_dict = {  
                                                "error": f'There was an error creating the timetable. Please ensure the number of lessons per week are of good estimates. Please ensure the routine of  teacher in your school is flexible. ',
                                            }
                                            timetable_errors.append(error_dict)

                                            result = createtimetable(theschool, tries_timetable)
                                            if not result:
                                                return False
                                    # If there was no collission, performs an addition of the lesson
                                    else:
                                        # Ensure this becomes one
                                        tries_teacher = 1
                                        lesson_dict = {}
                                        lesson_dict['teacher'] = thelesson_fromdb.teacher
                                        lesson_dict['subject'] = thelesson_fromdb.groupsubjects.subject
                                        lesson_dict['start_time'] = the_start_time
                                        lesson_dict['end_time'] = expected_time_tooend 

                                        # Update the classlessons
                                        classlessons.append(lesson_dict)

                                        # Loop though all teacherlessons
                                        for i in range(len(teacherlessons)):
                                            if teacherlessons[i]['teacherid'] == thelesson_fromdb.teacher.randomid:
                                                teacher_days = teacherlessons[i]['days']
                                                # Get the particular day
                                                for j in range(len(teacher_days)):
                                                    if (teacher_days[j]['theday'] == aroutine.day):
                                                        teacher_specificday = teacher_days[j][aroutine.day]

                                                        # Store teacher - day related info
                                                        teacher_dict = {}
                                                        teacher_dict['class'] = aclass
                                                        teacher_dict['start_time'] = the_start_time
                                                        teacher_dict['end_time'] = expected_time_tooend

                                                        teacher_specificday.append(teacher_dict)
                                                # break the loop after a match
                                                break

                                        # lessons number
                                        for alesson in lessons_number:
                                            # Update where there is a match
                                            if (alesson['groupsubjects'] == thelesson_fromdb.groupsubjects) and (alesson['theclass'] == thelesson_fromdb.theclass) and (alesson['teacher'] == thelesson_fromdb.teacher):
                                                alesson['current_number'] += 1
                                        
                                        # update the start time
                                        the_start_time = expected_time_tooend
                                            
                                # Try again in case of an error
                                # If the added number of lessons is greater than the max number specified by the user, the function tries again for all subjects. In case there is an issue still, the function deletes the current timetable and start the process of creating a timetable again.
                                else:
                                    # If this is the first try
                                    if tries_subjects == 1:
                                        starttimeconfirm = the_start_time
                                    
                                    if the_start_time == starttimeconfirm:
                                        tries_subjects += 1

                                    # If done this for all subjects
                                    if (tries_subjects == (len(all_class_subjects))):
                                        
                                        # Delete the timetable group
                                        newly_created = Timetablegroup.objects.get(id=newtimetable.id)
                                        newly_created.delete()
                                        tries_timetable += 1
                                        
                                        result = createtimetable(theschool, tries_timetable)
                                        if not result:
                                            return False
                    
                    # Add the lesson and breaks to the database                 
                    # Add all breaks
                    for i in range(len(allbreaks)):
                        newbreak = Timetablebreaks()
                        newbreak.timetablegroup = newtimetable
                        newbreak.breakname = allbreaks[i].breakname
                        newbreak.day = aroutine.day
                        newbreak.starttime = allbreaks[i].starttime
                        newbreak.endtime = allbreaks[i].endtime
                        newbreak.theclass = aclass
                        newbreak.save()
            
                    # For all lessons
                    for a in range(len(classlessons)):
                        lesson_start = classlessons[a]['start_time']
                        lesson_end = classlessons[a]['end_time']
                        newlesson = Timetablelessons()
                        newlesson.timetablegroup = newtimetable
                        newlesson.day = aroutine.day
                        newlesson.starttime = calculate_time(lesson_start.seconds) 
                        newlesson.endtime = calculate_time(lesson_end.seconds)
                        newlesson.theclass = aclass
                        newlesson.teacher = classlessons[a]['teacher']
                        newlesson.subject = classlessons[a]['subject']
                        newlesson.save()
    # Return True if all is well
    return True

# Arrange the timetable to display in templates
def arrangetimetable(thetimetable, theclass):
    # Get all breaks and lessons for this class
    day_for_lessons = Timetablelessons.objects.filter(timetablegroup__id=thetimetable.id, theclass__id=theclass.id)
    day_for_breaks = Timetablebreaks.objects.filter(timetablegroup__id=thetimetable.id, theclass__id=theclass.id)

    # Store all distinct days for this class
    all_days = []
    # Add all days
    for a in day_for_lessons:
        the_day = a.day
        if the_day not in all_days:
            all_days.append(a.day)

    # Add a day if only present in break and not lessons
    for b in day_for_breaks:
        theday = b.day
        if theday not in all_days:
            all_days.append(theday)

    # Store lessons for this classfor all days
    lesson_list = []
    # Loop for all days
    for aday in all_days:
        # Get all lessons for this day and this claa
        alllessons = Timetablelessons.objects.filter(timetablegroup__id=thetimetable.id, theclass__id=theclass.id, day=aday).order_by('starttime')
        allbreaks = Timetablebreaks.objects.filter(timetablegroup__id=thetimetable.id, theclass__id=theclass.id, day=aday).order_by('starttime')

        # Store sessions of this day
        day_sessions = []

        # Add all lessons to sessions
        for alesson in alllessons:
            day_sessions.append(alesson)

        # Set break index to zero
        breakindex = 0
        # Store number of breaks
        breakcount = allbreaks.count()

        # Insert all the breaks appropriately
        while (breakindex < breakcount):
            # Loop though all current sessions
            for i in range(len(day_sessions)):
                thisbreak = allbreaks[breakindex]
                # Store start time and end time of current break referring to
                break_start = thisbreak.starttime
                break_end = thisbreak.endtime

                # Store sessions start time and endtime
                session_start = day_sessions[i].starttime
                session_end = day_sessions[i].endtime

                # Insert before the current session
                if break_end == session_start:
                    day_sessions.insert(i, thisbreak)
                    # Stop inserting after reachiing all breaks
                    newbreakindex = breakindex + 1
                    if (newbreakindex < breakcount):
                        breakindex += 1
                    else:
                        breakindex += 1
                        break
                # Insert after the current session
                elif break_start == session_end:
                    insertindex = i + 1
                    day_sessions.insert(insertindex, thisbreak)
                    # Stop inserting after reachiing all breaks
                    newbreakindex = breakindex + 1
                    if (newbreakindex < breakcount):
                        breakindex += 1
                    else:
                        breakindex += 1
                        break

        sesson_dict = {}
        sesson_dict['day'] = aday
        sesson_dict['lessons'] = day_sessions

        # add to lesson list
        lesson_list.append(sesson_dict)

    return lesson_list