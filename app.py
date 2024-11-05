from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from waitress import serve
from time import sleep, time
import threading
import queue
import os
from config import Config
from flask_migrate import Migrate
from models import db, User
from auth import auth
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
import main
from werkzeug.security import check_password_hash, generate_password_hash  # Import for password checking and hashing

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

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
        # Update user profile details
        current_user.college_name = request.form['college_name']
        current_user.email = request.form['email']
        current_user.contact_number = request.form.get('phone', '')
        current_user.address = request.form.get('address', '')

        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename != '':
            picture = request.files['profile_picture']
            print(f"Received file: {picture.filename}")

            # Directory for saving profile pictures
            picture_dir = os.path.join(app.root_path, 'static/profile_pics')
            os.makedirs(picture_dir, exist_ok=True)

            # Save picture with unique filename based on user ID and timestamp
            picture_filename = f"{current_user.id}_{int(time())}_{picture.filename}"
            picture_path = os.path.join(picture_dir, picture_filename)

            # Save the picture to the specified path
            picture.save(picture_path)
            print(f"Profile picture saved at: {picture_path}")

            # Update profile picture path in the database
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
            print(f"Database update error: {e}")

        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', user=current_user)

@app.route('/update_details', methods=['GET', 'POST'])
@login_required
def update_details():
    if request.method == 'POST':
        print("Received form data:")
        print(f"College Name: {request.form['college_name']}")
        print(f"Email: {request.form['email']}")
        print(f"Phone: {request.form.get('phone', '')}")
        print(f"Address: {request.form.get('address', '')}")

        current_user.college_name = request.form['college_name']
        current_user.email = request.form['email']
        current_user.contact_number = request.form.get('phone', '')
        current_user.address = request.form.get('address', '')

        try:
            db.session.commit()
            flash('Details updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating details: {e}', 'danger')
            print(f"Database update error: {e}")

        return redirect(url_for('dashboard'))

    return render_template('update_details.html', user=current_user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        # Verify the old password
        if check_password_hash(current_user.password, old_password):
            # Hash the new password before saving
            current_user.password = generate_password_hash(new_password)  
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Old password is incorrect!', 'danger')

    return render_template('change_password.html', user=current_user)

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
    # Serve the app with Waitress on port 5000
    serve(app, host='0.0.0.0', port=5000)
