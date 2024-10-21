from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import urlparse, urljoin
from models import User, Course, Registration, Review
from forms import LoginForm, RegistrationForm, CourseForm, AccountSettingsForm, AnnouncementForm, ReviewForm
from extensions import db
from datetime import datetime
from utils import send_announcement_email

main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__)

# ... (rest of the routes remain the same)
