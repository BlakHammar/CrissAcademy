from flask_mail import Message
from flask import current_app, url_for

def send_confirmation_email(user, course):
    msg = Message('Course Registration Confirmation',
                  recipients=[user.email])
    msg.body = f"""
    Dear {user.username},

    Thank you for registering for the course: {course.title}

    Course Details:
    Date: {course.date}
    Zoom Link: {course.zoom_link}
    Materials: {course.materials_link}

    We look forward to seeing you in the course!

    Best regards,
    Criss Academy Team
    """
    current_app.extensions['mail'].send(msg)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    msg.body = f"""To reset your password, visit the following link:
{url_for('main.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
"""
    current_app.extensions['mail'].send(msg)

def send_announcement_email(user, course, announcement):
    msg = Message(f'Announcement: {course.title}',
                  recipients=[user.email])
    msg.body = f"""
    Dear {user.username},

    There is an important announcement regarding your enrolled course: {course.title}

    Announcement:
    {announcement}

    If you have any questions, please contact your instructor.

    Best regards,
    Criss Academy Team
    """
    current_app.extensions['mail'].send(msg)
