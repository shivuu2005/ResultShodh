from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import logging

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Blueprint
auth = Blueprint('auth', __name__)

# Registration Form
class RegistrationForm(FlaskForm):
    college_name = StringField('College Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    contact_number = StringField('Contact Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Register')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        college_name = form.college_name.data
        email = form.email.data
        password = form.password.data
        contact_number = form.contact_number.data
        address = form.address.data

        # Length checks
        if len(email) > 150:
            flash('Email exceeds maximum length of 150 characters.', 'error')
            return redirect(url_for('auth.register'))

        if len(password) > 150:
            flash('Password exceeds maximum length of 150 characters.', 'error')
            return redirect(url_for('auth.register'))

        logging.info(f"Registering new user: {college_name}")

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'error')
            return redirect(url_for('auth.register'))

        # Create a new user with hashed password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            college_name=college_name,
            email=email,
            password=hashed_password,
            contact_number=contact_number,
            address=address
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

# The rest of your code...


# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('dashboard' if not current_user.is_admin else 'admin_dashboard'))

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        logging.info(f"Login attempt for email: {email}")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard' if not user.is_admin else 'admin_dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'error')

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logging.info(f"User {current_user.college_name} logged out")
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
