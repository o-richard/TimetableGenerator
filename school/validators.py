from django.core.exceptions import ValidationError

# Ensure the size of uploaded school logo is less than 2MB.
def validate_logo(value):
    filesize = value.size

    if filesize > 2097152:
        raise ValidationError("The maximum image size is 2MB")
    else:
        return value