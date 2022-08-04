from .models import User, School, Teachers
import random

#generate a unique random id for a registering user
def generate_random_id():
    random_id = ''
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    random_id_length = 8
    for y in range(random_id_length):
        random_id += characters[random.randint(0, len(characters)-1)]
    checkord = User.objects.filter(randomid=random_id).count()
    if checkord > 0:
        generate_random_id()
    return random_id

#generate a unique random id for a adding school
def generate_random_id_forschool():
    random_id = ''
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    random_id_length = 8
    for y in range(random_id_length):
        random_id += characters[random.randint(0, len(characters)-1)]
    checkord = School.objects.filter(randomid=random_id).count()
    if checkord > 0:
        generate_random_id_forschool()
    return random_id

#generate a unique random id for a adding teacher
def generate_random_id_forteacher():
    random_id = ''
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    random_id_length = 8
    for y in range(random_id_length):
        random_id += characters[random.randint(0, len(characters)-1)]
    checkord = Teachers.objects.filter(randomid=random_id).count()
    if checkord > 0:
        generate_random_id_forteacher()
    return random_id