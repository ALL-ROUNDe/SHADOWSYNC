from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, time, json
from functools import wraps
from ftplib import FTP
import io

app = Flask(__name__)
app.secret_key = 'secreat_pass'

# --- FOLDER SETUP ---
BASE_DIR = '/share/uploads'  # Change this to your target upload location
FOLDERS = {
    'movies': os.path.join(BASE_DIR, 'movies'),     # you can change this
    'allfiles': os.path.join(BASE_DIR, 'allfiles')
}
for path in FOLDERS.values():
    os.makedirs(path, exist_ok=True)

# --- USER STORAGE ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_PATH, 'shadowsync/users.json')

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

if not os.path.exists(USERS_FILE):
    USERS = {
        'admin': {
            'pw': generate_password_hash('adminpass'),
            'role': 'admin'
        }
    }
    save_users(USERS)
else:
    USERS = load_users()

# --- AUTH DECORATOR ---
def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get('user'):
            return redirect(url_for('login'))
        return f(*a, **k)
    return w

# --- UTILITIES ---
def format_size(size):
    for unit in ['bytes', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def get_files(folder):
    files = []
    for fn in sorted(os.listdir(folder)):
        path = os.path.join(folder, fn)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append({
                'name': fn,
                'size_raw': stat.st_size,
                'size': format_size(stat.st_size),
                'mtime': time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
            })
    return files

# --- ROUTES ---

@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = USERS.get(u)
        if user and check_password_hash(user['pw'], p):
            session['user'] = u
            session['role'] = user['role']
            flash('Logged in', 'success')
            return redirect(url_for('folders'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
@login_required
def register():
    if session.get('role') != 'admin':
        flash('Admin access only', 'error')
        return redirect(url_for('folders'))

    if request.method == 'POST':
        uname = request.form['username']
        pw = request.form['password']
        role = request.form['role']
        if uname in USERS:
            flash('User already exists', 'error')
        else:
            USERS[uname] = {
                'pw': generate_password_hash(pw),
                'role': role
            }
            save_users(USERS)
            flash(f'User {uname} created', 'success')
        return redirect(url_for('admin'))

    return render_template('admin.html', users=USERS)

@app.route('/admin')
@login_required
def admin():
    if session.get('role') != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('folders'))
    return render_template('admin.html', users=USERS)

@app.route('/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if session.get('role') != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('folders'))

    if username == 'admin':
        flash('Cannot delete default admin user', 'error')
    elif username not in USERS:
        flash('User not found', 'error')
    else:
        USERS.pop(username)
        save_users(USERS)
        flash(f'User {username} deleted', 'success')
    return redirect(url_for('admin'))

@app.route('/folders')
@login_required
def folders():
    folder_data = {}
    total_files = 0
    total_size = 0

    for key, path in FOLDERS.items():
        files = get_files(path)
        folder_data[key] = files
        total_files += len(files)
        total_size += sum(f['size_raw'] for f in files)

    return render_template(
        'folders.html',
        folders=FOLDERS.keys(),
        folder_data=folder_data,
        total_files=total_files,
        total_size=total_size,
        user=session['user'],
        role=session['role']
    )

@app.route('/folder/<folder_key>')
@login_required
def folder(folder_key):
    if folder_key not in FOLDERS:
        flash('No such folder', 'error')
        return redirect(url_for('folders'))
    return render_template(
        'folder.html',
        folder_key=folder_key,
        files=get_files(FOLDERS[folder_key]),
        user=session['user'],
        role=session['role']
    )

@app.route('/upload/<folder_key>', methods=['POST'])
@login_required
def upload(folder_key):
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('folder', folder_key=folder_key))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('folder', folder_key=folder_key))

    folder = FOLDERS.get(folder_key)
    if folder is None:
        abort(404)

    os.makedirs(folder, exist_ok=True)

    filename = secure_filename(file.filename)
    dest = os.path.join(folder, filename)
    print(request.files)
    print(file.filename)
    print(folder)
    print(dest)
    try:
        print(f"Saving to: {dest}")

        with open(dest, "wb") as out:
            total = 0

            while True:
                chunk = file.stream.read(16 * 1024 * 1024)
                if not chunk:
                    break

                total += len(chunk)
                out.write(chunk)

        print(f"Wrote {total} bytes")
        print("Exists:", os.path.exists(dest))
        print("Size:", os.path.getsize(dest))

        flash(f"Uploaded {filename}", "success")

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(str(e), "error")

        

    return redirect(url_for('folder', folder_key=folder_key))




@app.route('/download/<folder_key>/<filename>')
@login_required
def download(folder_key, filename):
    folder = FOLDERS.get(folder_key)
    if not folder:
        flash('Invalid folder', 'error')
        return redirect(url_for('folders'))
    return send_from_directory(folder, filename, as_attachment=True)

@app.route('/delete_file/<folder_key>/<filename>', methods=['POST'])
@login_required
def delete_file(folder_key, filename):
    if session.get('role') != 'admin':
        flash('Only admins can delete files', 'error')
        return redirect(url_for('folder', folder_key=folder_key))

    folder = FOLDERS.get(folder_key)
    if not folder:
        flash('Invalid folder', 'error')
        return redirect(url_for('folders'))

    file_path = os.path.join(folder, filename)
    try:
        os.remove(file_path)
        flash(f'{filename} deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting file: {e}', 'error')

    return redirect(url_for('folder', folder_key=folder_key))

@app.route('/upload-progress/<folder_key>')
@login_required
def upload_progress(folder_key):
    if folder_key not in FOLDERS:
        flash('Invalid folder', 'error')
        return redirect(url_for('folders'))
    return render_template('upload_progress.html', folder_key=folder_key, user=session['user'])



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
