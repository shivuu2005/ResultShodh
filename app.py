from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from waitress import serve
from time import sleep, time
import threading
import queue
import os
from flask_migrate import Migrate
from config import Config
from models import db, User
from flask_wtf import FlaskForm
from auth import auth
from wtforms import StringField, FileField, SubmitField,PasswordField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileAllowed
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
from flask_wtf import CSRFProtect  # Import CSRF protection
from werkzeug.security import check_password_hash, generate_password_hash

import main

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Login manager setup
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database and migration setup
db.init_app(app)
migrate = Migrate(app, db)

# Register auth blueprint
app.register_blueprint(auth, url_prefix='/auth')

# Initialize queue and task storage
task_queue = queue.Queue()
task_data = {}

# Background worker to process tasks
def worker():
    while True:
        try:
            uuid = task_queue.get()
            if uuid in task_data:
                task_data[uuid]['task'].start()
                task_queue.task_done()
        except Exception as e:
            print(f"Worker encountered an error: {e}")

# Cleanup thread to remove stale tasks
def janitor():
    while True:
        sleep(2700)  # 45 minutes
        now = time()
        stale_tasks = [uuid for uuid, data in task_data.items() if now - data['timestamp'] > 2700]
        for uuid in stale_tasks:
            del task_data[uuid]

# Define routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/form')
@login_required
def form():
    return render_template('form.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        current_user.college_name = request.form['college_name']
        current_user.email = request.form['email']
        current_user.contact_number = request.form.get('phone', '')
        current_user.address = request.form.get('address', '')

        if 'profile_picture' in request.files and request.files['profile_picture'].filename != '':
            picture = request.files['profile_picture']
            picture_dir = os.path.join(app.root_path, 'static/profile_pics')
            os.makedirs(picture_dir, exist_ok=True)
            picture_filename = f"{current_user.id}_{int(time())}_{picture.filename}"
            picture_path = os.path.join(picture_dir, picture_filename)
            picture.save(picture_path)
            current_user.profile_picture = f"profile_pics/{picture_filename}"
        else:
            if not current_user.profile_picture:
                current_user.profile_picture = "default.png"

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')

        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', user=current_user)

class UpdateDetailsForm(FlaskForm):
    college_name = StringField('College Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(10)])
    address = StringField('Address')
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Update Profile')
@app.route('/update_details', methods=['GET', 'POST'])
@login_required
def update_details():
    form = UpdateDetailsForm()
    
    if form.validate_on_submit():
        current_user.college_name = form.college_name.data
        current_user.email = form.email.data
        current_user.contact_number = form.phone.data
        current_user.address = form.address.data

        # Save profile picture if uploaded
        profile_picture = form.profile_picture.data
        if profile_picture:
            # Save profile_picture file (implement this part as per your file storage needs)
            pass

        try:
            db.session.commit()
            flash('Details updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating details: {e}', 'danger')

        return redirect(url_for('dashboard'))

    # Pre-fill the form with current user's data
    form.college_name.data = current_user.college_name
    form.email.data = current_user.email
    form.phone.data = current_user.contact_number
    form.address.data = current_user.address

    return render_template('update_details.html', form=form, user=current_user)


# Assuming User model with SQLAlchemy session
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        # Check if the old password matches the one in the database
        if check_password_hash(current_user.password, old_password):
            # Update the password with the new hashed password
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Old password is incorrect!', 'danger')

    return render_template('change_password.html', user=current_user)


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

@app.route('/change_password', methods=['GET', 'POST'], endpoint='change_password_route')
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        old_password = form.old_password.data
        new_password = form.new_password.data

        # Verify the old password
        if check_password_hash(current_user.password, old_password):
            # Update the password in the database
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Old password is incorrect!', 'danger')

    return render_template('change_password.html', form=form)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    return render_template('admin_dashboard.html', user=current_user)

@app.route('/requests', methods=['POST'])
def requests():
    try:
        uuid = main.randomString()
        department = int(request.json['department'])
        semester = int(request.json['semester'])
        maxroll = int(request.json['maxroll'])
        roll_prefix = request.json['rollPrefix']

        task_data[uuid] = {
            'task': main.resultProcessor(department, semester, maxroll, roll_prefix),
            'timestamp': time()
        }
        task_queue.put(uuid)

        return jsonify({'uuid': uuid}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/progress')
def progress():
    uuid = request.args.get('uuid')
    if uuid in task_data:
        task = task_data[uuid]['task']
        return jsonify({"progress": task.progress.progress, "max": task.maxroll, "status": "200"})
    else:
        return jsonify({"progress": "0", "max": "0", "status": "901"})

@app.route('/getfile')
def getfile():
    uuid = request.args.get('uuid')
    if uuid in task_data:
        file_path = os.path.join(app.root_path, 'results', f"{uuid}.csv")
        if os.path.exists(file_path):
            return jsonify({"status": "200", "file_path": file_path})
        else:
            return jsonify({"status": "404", "message": "File not found."}), 404
    else:
        return jsonify({"status": "404", "message": "Invalid UUID."}), 404

# Start background threads
threading.Thread(target=worker, daemon=True).start()
threading.Thread(target=janitor, daemon=True).start()

if __name__ == '__main__':
    # Serve the app with Waitress on port 8080
    
    serve(app, host='0.0.0.0', port=8080)
