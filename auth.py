from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

# Initialize the Blueprint
auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        college_name = request.form.get('college_name')
        email = request.form.get('email')
        password = request.form.get('password')
        contact_number = request.form.get('contact_number')  # Get contact number
        address = request.form.get('address')  # Get address

        print(f"Registering new user: {college_name}")  # Debug statement

        # Check if the email or college name is already registered
        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(college_name=college_name).first():
            flash('College name is already taken.', 'error')
            return redirect(url_for('auth.register'))

        # Create a new user
        new_user = User(
            college_name=college_name,
            email=email,
            password=password,
            contact_number=contact_number,  # Save contact number
            address=address  # Save address
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard' if not current_user.is_admin else 'admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Login attempt for email: {email}")  # Debug statement
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:  # Note: This is without password hashing (insecure)
            login_user(user)
            return redirect(url_for('dashboard' if not user.is_admin else 'admin_dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'error')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    print(f"User {current_user.college_name} logged out")  # Debug statement
    logout_user()
    return redirect(url_for('auth.login'))
