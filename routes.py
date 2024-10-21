from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import urlparse, urljoin
from models import User, Course, Registration, Review
from forms import LoginForm, RegistrationForm, CourseForm, AccountSettingsForm, AnnouncementForm, ReviewForm
from app import db
from datetime import datetime
from utils import send_announcement_email

main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash,
                                        form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(
                url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data,
                    email=form.email.data,
                    password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in',
              'success')
        return redirect(url_for('main.login'))
    return render_template('signup.html', form=form)


@main.route('/instructor_dashboard')
@login_required
def instructor_dashboard():
    # Allow access if the user is an admin or instructor
    if not (current_user.is_instructor or current_user.is_admin):
        flash(
            'Access denied. You must be an instructor or admin to view this page.',
            'danger')
        return redirect(url_for('main.index'))

    # Admins can see all courses; instructors see only their own
    if current_user.is_admin:
        instructor_courses = Course.query.order_by(Course.date.desc()).all()
    else:
        instructor_courses = Course.query.filter_by(
            instructor_id=current_user.id).order_by(Course.date.desc()).all()

    course_details = []
    for course in instructor_courses:
        enrollments = Registration.query.filter_by(course_id=course.id).count()
        revenue = enrollments * course.price
        course_details.append({
            'course':
            course,
            'enrollments':
            enrollments,
            'revenue':
            revenue,
            'status':
            'Upcoming' if course.date > datetime.now() else 'Past'
        })

    return render_template('instructor/dashboard.html',
                           course_details=course_details)


@main.route('/instructor/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if not (current_user.is_instructor or current_user.is_admin):
        flash(
            'Access denied. You must be an instructor or admin to add courses.',
            'danger')
        return redirect(url_for('main.index'))

    form = CourseForm()
    if form.validate_on_submit():
        course = Course(title=form.title.data,
                        description=form.description.data,
                        date=form.date.data,
                        price=form.price.data,
                        zoom_link=form.zoom_link.data,
                        materials_link=form.materials_link.data,
                        instructor_id=current_user.id)
        db.session.add(course)
        db.session.commit()
        flash('Course added successfully.', 'success')
        return redirect(url_for('main.instructor_dashboard'))
    return render_template('instructor/add_course.html', form=form)


@main.route('/instructor/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    # Allow only the instructor or admin to edit the course
    course = Course.query.get_or_404(course_id)

    if not current_user.is_admin and course.instructor_id != current_user.id:
        flash(
            'Access denied. You can only edit your own courses unless you are an admin.',
            'danger')
        return redirect(url_for('main.instructor_dashboard'))

    form = CourseForm(obj=course)
    if form.validate_on_submit():
        form.populate_obj(course)
        db.session.commit()
        flash('Course updated successfully.', 'success')
        return redirect(url_for('main.instructor_dashboard'))

    return render_template('instructor/edit_course.html',
                           form=form,
                           course=course)


@main.route('/instructor/course_enrollments/<int:course_id>')
@login_required
def course_enrollments(course_id):
    if not (current_user.is_instructor or current_user.is_admin):
        flash(
            'Access denied. You must be an instructor or admin to view course enrollments.',
            'danger')
        return redirect(url_for('main.index'))

    course = Course.query.get_or_404(course_id)
    enrollments = Registration.query.filter_by(course_id=course_id).order_by(
        Registration.registration_date.desc()).all()
    return render_template('instructor/course_enrollments.html',
                           course=course,
                           enrollments=enrollments)


@main.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    form = AccountSettingsForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        if form.new_password.data:
            current_user.password_hash = generate_password_hash(
                form.new_password.data)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account_settings'))
    elif request.method == 'GET':
        form.email.data = current_user.email
    return render_template('account_settings.html', form=form)


@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@main.route('/instructor/course/<int:course_id>/cancel', methods=['POST'])
@login_required
def cancel_course(course_id):
    if not (current_user.is_instructor or current_user.is_admin):
        flash(
            'Access denied. You must be an instructor or admin to cancel courses.',
            'danger')
        return redirect(url_for('main.index'))

    course = Course.query.get_or_404(course_id)
    course.is_cancelled = True
    db.session.commit()

    flash(f'Course "{course.title}" has been cancelled.', 'success')
    return redirect(url_for('main.instructor_dashboard'))


@main.route('/instructor/course/<int:course_id>/reschedule', methods=['POST'])
@login_required
def reschedule_course(course_id):
    # Allow only admins or the course instructor to reschedule
    course = Course.query.get_or_404(course_id)

    if not current_user.is_admin and course.instructor_id != current_user.id:
        flash(
            'Access denied. You can only reschedule your own courses unless you are an admin.',
            'danger')
        return redirect(url_for('main.instructor_dashboard'))

    new_date = request.form.get('new_date')
    if new_date:
        course.date = datetime.strptime(new_date, '%Y-%m-%dT%H:%M')
        db.session.commit()
        flash(
            f'Course "{course.title}" has been rescheduled to {course.date}.',
            'success')
    else:
        flash('Invalid date format.', 'danger')

    return redirect(url_for('main.instructor_dashboard'))


@main.route('/instructor/course/<int:course_id>/announce',
            methods=['GET', 'POST'])
@login_required
def course_announcement(course_id):
    # Allow only admins or the course instructor to make announcements
    course = Course.query.get_or_404(course_id)

    if not current_user.is_admin and course.instructor_id != current_user.id:
        flash(
            'Access denied. You can only make announcements for your own courses unless you are an admin.',
            'danger')
        return redirect(url_for('main.instructor_dashboard'))

    form = AnnouncementForm()
    if form.validate_on_submit():
        enrollments = Registration.query.filter_by(course_id=course_id).all()
        for enrollment in enrollments:
            send_announcement_email(enrollment.user, course, form.message.data)
        flash('Announcement sent successfully.', 'success')
        return redirect(url_for('main.instructor_dashboard'))

    return render_template('instructor/announcement.html',
                           form=form,
                           course=course)


@main.route('/course/<int:course_id>', methods=['GET', 'POST'])
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    form = ReviewForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You must be logged in to submit a review.', 'warning')
            return redirect(url_for('main.login'))

        existing_review = Review.query.filter_by(user_id=current_user.id,
                                                 course_id=course.id).first()
        if existing_review:
            flash('You have already submitted a review for this course.',
                  'warning')
        else:
            review = Review(user_id=current_user.id,
                            course_id=course.id,
                            rating=form.rating.data,
                            comment=form.comment.data)
            db.session.add(review)
            db.session.commit()
            flash('Your review has been submitted.', 'success')
        return redirect(url_for('main.course_detail', course_id=course.id))

    reviews = Review.query.filter_by(course_id=course.id).order_by(
        Review.created_at.desc()).all()
    avg_rating = db.session.query(db.func.avg(
        Review.rating)).filter(Review.course_id == course.id).scalar()

    return render_template('course_detail.html',
                           course=course,
                           form=form,
                           reviews=reviews,
                           avg_rating=avg_rating)


@main.route('/register_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def register_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        registration = Registration(user_id=current_user.id,
                                    course_id=course.id)
        db.session.add(registration)
        db.session.commit()
        flash('You have successfully registered for this course!', 'success')
        return redirect(url_for('main.course_detail', course_id=course.id))
    return render_template('register.html', course=course)


@admin.route('/dashboard')
@login_required
def dashboard():
    try:
        courses = Course.query.all()
        return render_template('admin/dashboard.html', courses=courses)
    except Exception as e:
        print(f"Template Error: {e}")
        return "An error occurred", 500


# Delete accounts route
@admin.route('/delete_accounts', methods=['POST'])
@login_required
def delete_accounts():
    if not current_user.is_admin:
        flash('Access denied. You must be an admin to delete accounts.',
              'danger')
        return redirect(url_for('admin.dashboard'))

    try:
        # Delete all users except Admins and Instructors
        User.query.filter(
            User.is_admin == False,  # Keep admins
            User.is_instructor == False  # Keep instructors
        ).delete()

        db.session.commit()
        flash('All non-admin and non-instructor accounts have been deleted.',
              'success')

    except Exception as e:
        print(f"Error deleting accounts: {e}")
        flash('An error occurred while deleting accounts.', 'danger')

    return redirect(url_for('admin.dashboard'))
