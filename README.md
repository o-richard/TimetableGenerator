# TimetableGenerator

> This is a django project used to generate timetables for a school which could be output as a pdf and downloaded.

![Timetable](screenshots/timetable.jpg "A generated timetable output for a class")

# Requirements  (Prerequisites)
Tools and packages required to successfully install this project.
For example:
* Python 3.10.4 and up [Install](https://www.python.org/downloads/)

# Installation
Clone this project in your local machine. Crete a virtual enviroment and enter it.

Run the following command in the virtual environment to install all requirements of this project.

`pip install -r requirements.txt`

Create a `.env` file in your projects root folder.

    SECRET_KEY = YOUR_SECRET_KEY
    DEBUG = A boolean value
    ALLOWED_HOSTS= A list of comma separated hosts to allow.

Ensure you are in the project's root folder when you run the following command.

`python manage.py runserver`

Navigate to :

`127.0.0.1:8000/login`

* There are two accounts present in the database.

    * An account with admin priviledges and can access `127.0.0.1:8000/admin/`
        
        * Username - user
        * Password - user123.
    * An account with no admin priviledges(The account that contains the sample data)

        * Username - test
        * Password - test123.

In case you want to create an administator account, run the following command in your terminal and filll the requested information. 

* `python manage.py createsuperuser`

* Afterwards, navigate to `127.0.0.1:8000/admin/` to the User model and add a randomid for the newly created super user. (A randomid is a unique randomly generated string which contains eight characters which are a mixture of letters and nummbers). Since by default , Django does not generate one.

In case you want a normal account with no admin priviledges, navigate to `127.0.0.1:8000/register/` and fill the form.

![register and login page](screenshots/login.jpg "Registration and Log in")

You may want to modify the values for the last four variables in your settings.py. Thepurpose of the four variables is to reduce the strain of typing values manuaaly which may otherwise be redundant in your school.

![settings.py file](screenshots/settings.png "Settings.py file")

* DEFAULT_TEACHER_START_TIME - Specifies the default start time to use for every teacher's routine as you render the form in your browser.
* DEFAULT_TEACHER_END_TIME - Specifies the default end time to use for every teacher's routine as you render the form in your browser.
* DEFAULT_ROUTINE_START_TIME - Specifies the default start time to use for every group's routine as you render the form in your browser.
* DEFAULT_ROUTINE_END_TIME - Specifies the default end time to use for every group's routine as you render the form in your browser.

# Screenshots
Here are some of the screenshots of the application.

![Home page](screenshots/homepage.png "Home Page")

![School page](screenshots/timetable_2.jpg "Schools home page")

# Features
- Lesson specification at a particular time.
- Generate random colors for a given subject for a school for visual appeal as one generates a timetable.
- Accommodate all days of the week to fit any school's routine.
- Specify the routine of a particular teacher to generate a timetable fitting his/her schedule.
- Check if a school can generate its own timetable and reports on its errors in case of any.
- Flexibility - One can specify how long a given group of a school should start or stop their daily sessions.

# Usage example

- Register for an account/ Log in if you already have an account.
- Create a school. (A school logo is optional and the school name you enter should be unique in your account).
    > When you view a school, you should see what you need to add first before generating a timetable.

    ![School home page](screenshots/school_home.png "School home page")

    - Add subjects in your school. The subject name you enter should be unique for your school.  You can only delete a subject, if you delete the timetable using that subject. However, you can edit the subject's details.
    - Add streams in your school. At least all classes in a school should have a stream. The stream name you entered should be unique for that school.  You can only delete a stream, if you delete the class using that stream. However, you can edit the stream's details.
    - Add teachers in your school. As you add a teacher, you should specify for each day, the teacher's routine. You can only delete a teacher, if you delete the timetable using that teacher. However, you can edit the teacher's details.
    - Add groups in your school. A group is where you define the routine, classes, breaks and lessons since a school may have different classes having their own routine.

    ---

    ![School](screenshots/school_1.jpg)

    ![School](screenshots/school_2.jpg)

    > When you do all the above steps, the school home page will change as follows. The page will show you, what for each group to generate a timetable

    ![School home page example 2](screenshots/school_home2.png "School home page example 2")

- For each group you have created:

    - Add subjects to the group. The subjects list is from the subjects you have in your school. A subject is only added once in a group.
    - Add classes. A class name of a particular stream only exists once in a given group. A class teacher can only have one class in that group. You can only delete a class, if you delete the timetable using that class. However, you can edit the class's details.
    - Add a routine for all days to include in your timetable with appropriate times. The routine of a particular day is chosen only once in that group.
    - Add lessons in that group. For a given class and a given subject, there is only one teacher. The number of lessons per week should be of good estimates lest you have an error as you generate your timetable.
    - You may add lesson specification if you wish to. The chosen period should be within the routine of a day.
    - You may add breaks for a particular group if you wish to. The chosen period should be within the routine of a given day.

    ---

    ![School Group](screenshots/group_1.jpg)

    ![School Group](screenshots/group_2.jpg)

- If you have done all the above steps, you may ***check if your school meets the reqirements to generate a timetable*** in the school's homepage.
- If you meet all requirements, you may generate a timetable. Any erros will be reported in case they occur.

# Project Structure

The django project is divide in to four apps.

* frontend - Contain the all the templates used by the project.
* groups - Contain all school groups related information
* schools - Contin user-related and school-related information.
* timetable - Contain timetable-related information with the algorithims on timetable oprations.

# Built With
1. [Django](https://djangoproject.com/) - The Django framework

# Author

The author of this project is Richard Odhiambo.

 You can find me here at:
[Github](https://github.com/o-richard)
[LinkedIn](https://www.linkedin.com/in/richard-o-505bb3172/)

# License

This project is licensed under the MIT License.