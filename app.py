from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
import math
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "instance", "complaints.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Base location coordinates (RPSU)
BASE_LAT = 23.601004
BASE_LON = 90.498348

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])


    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  
    return c * r

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/location", methods=["POST"])
def receive_location():
    data = request.get_json()

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")

    if latitude is None or longitude is None:
        return jsonify({
            "status": "error",
            "message": "Invalid location data"
        }), 400

    # Calculate distance from base location
    distance = haversine(BASE_LAT, BASE_LON, latitude, longitude)
    allowed = distance <= 2.0  # Within 2km radius

    return jsonify({
        "status": "success",
        "allowed": allowed,
        "distance": distance
    })

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    complaint = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    image_path = db.Column(db.String(200), nullable=True)
    agree_count = db.Column(db.Integer, default=0)
    disagree_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    flagged_at = db.Column(db.DateTime, nullable=True)  # Set when disagree% >= 65%

    def to_dict(self):
        return {
            'id': self.id,
            'reference_id': self.reference_id,
            'department': self.department,
            'category': self.category,
            'subject': self.subject,
            'complaint': self.complaint,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.strftime('%B %d, %Y at %I:%M %p')
        }

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)  # 'agree' or 'disagree'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'complaint_id', name='unique_user_complaint_vote'),)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Admin session decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def update_disagree_flag(complaint):
    """Flag a complaint if disagree votes are >= 65% of total votes, unflag otherwise."""
    total = complaint.agree_count + complaint.disagree_count
    if total > 0 and (complaint.disagree_count / total) >= 0.65:
        if complaint.flagged_at is None:
            complaint.flagged_at = datetime.utcnow()
    else:
        complaint.flagged_at = None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_complaint():
    try:
        data = request.form

        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '_' + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                image_path = 'uploads/' + unique_filename

        # Generate unique reference ID
        reference_id = f"RPSU-{str(uuid.uuid4())}"

        # Create anonymous complaint
        complaint = Complaint(
            reference_id=reference_id,
            department=data.get('department'),
            category=data.get('category'),
            subject=data.get('subject'),
            complaint=data.get('complaint'),
            priority=data.get('priority'),
            status='pending',
            image_path=image_path
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reference_id': reference_id,
            'message': 'Complaint submitted anonymously'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/admin')
@admin_required
def admin():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('admin.html', complaints=complaints)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin.username
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/settings', methods=['POST'])
@admin_required
def admin_settings():
    current_password = request.form.get('current_password')
    new_username = request.form.get('new_username', '').strip()
    new_password = request.form.get('new_password', '').strip()

    admin = Admin.query.filter_by(username=session.get('admin_username')).first()
    if not admin or not admin.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401

    if not new_username and not new_password:
        return jsonify({'success': False, 'message': 'Please provide a new username or password to update'}), 400

    if new_username:
        if Admin.query.filter_by(username=new_username).first():
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        admin.username = new_username
        session['admin_username'] = new_username

    if new_password:
        admin.set_password(new_password)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Settings updated successfully'})

@app.route('/admin/complaint/<int:id>')
@admin_required
def view_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    return render_template('view_complaint.html', complaint=complaint)

@app.route('/admin/update_status/<int:id>', methods=['POST'])
@admin_required
def update_status(id):
    try:
        complaint = Complaint.query.get_or_404(id)
        new_status = request.form.get('status')
        complaint.status = new_status
        db.session.commit()
        return redirect(url_for('admin'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/complaints')
def api_complaints():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return jsonify([c.to_dict() for c in complaints])

@app.route('/api/stats')
def api_stats():
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='pending').count()
    resolved = Complaint.query.filter_by(status='resolved').count()
    in_progress = Complaint.query.filter_by(status='in_progress').count()

    return jsonify({
        'total': total,
        'pending': pending,
        'resolved': resolved,
        'in_progress': in_progress
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        student_id = request.form.get('student_id')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate email domain
        if not email.endswith('@rpsu.edu.bd'):
            return jsonify({'success': False, 'message': 'Please use a valid @rpsu.edu.bd email address'}), 400

        # Validate password match
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        if User.query.filter_by(student_id=student_id).first():
            return jsonify({'success': False, 'message': 'Student ID already registered'}), 400

        user = User(name=name, student_id=student_id, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return jsonify({'success': True, 'message': 'Registration successful'})
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'message': 'Login successful'})
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/feed')
@login_required
def feed():
    complaints = Complaint.query.order_by(Complaint.agree_count.desc()).all()
    # Build a map of complaint_id -> vote_type for the current user
    user_votes = {v.complaint_id: v.vote_type for v in Vote.query.filter_by(user_id=current_user.id).all()}
    return render_template('feed.html', complaints=complaints, user_votes=user_votes)

@app.route('/api/complaint/<int:id>/agree', methods=['POST'])
@login_required
def agree_complaint(id):
    try:
        complaint = Complaint.query.get_or_404(id)
        existing_vote = Vote.query.filter_by(user_id=current_user.id, complaint_id=id).first()

        if existing_vote:
            if existing_vote.vote_type == 'agree':
                # Already agreed — remove vote (toggle off)
                complaint.agree_count -= 1
                db.session.delete(existing_vote)
                user_vote = None
            else:
                # Switching from disagree to agree
                complaint.disagree_count -= 1
                complaint.agree_count += 1
                existing_vote.vote_type = 'agree'
                user_vote = 'agree'
        else:
            # New vote
            complaint.agree_count += 1
            new_vote = Vote(user_id=current_user.id, complaint_id=id, vote_type='agree')
            db.session.add(new_vote)
            user_vote = 'agree'

        update_disagree_flag(complaint)
        db.session.commit()
        return jsonify({
            'success': True,
            'agree_count': complaint.agree_count,
            'disagree_count': complaint.disagree_count,
            'user_vote': user_vote
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/complaint/<int:id>/disagree', methods=['POST'])
@login_required
def disagree_complaint(id):
    try:
        complaint = Complaint.query.get_or_404(id)
        existing_vote = Vote.query.filter_by(user_id=current_user.id, complaint_id=id).first()

        if existing_vote:
            if existing_vote.vote_type == 'disagree':
                # Already disagreed — remove vote (toggle off)
                complaint.disagree_count -= 1
                db.session.delete(existing_vote)
                user_vote = None
            else:
                # Switching from agree to disagree
                complaint.agree_count -= 1
                complaint.disagree_count += 1
                existing_vote.vote_type = 'disagree'
                user_vote = 'disagree'
        else:
            # New vote
            complaint.disagree_count += 1
            new_vote = Vote(user_id=current_user.id, complaint_id=id, vote_type='disagree')
            db.session.add(new_vote)
            user_vote = 'disagree'

        update_disagree_flag(complaint)
        db.session.commit()
        return jsonify({
            'success': True,
            'agree_count': complaint.agree_count,
            'disagree_count': complaint.disagree_count,
            'user_vote': user_vote
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Initialize database
with app.app_context():
    db.create_all()
    # Seed default admin account if none exists
    if not Admin.query.first():
        default_admin = Admin(username='admin')
        default_admin.set_password('admin123')
        db.session.add(default_admin)
        db.session.commit()

# Background job: delete complaints flagged with 65%+ disagree for 5+ days
def auto_delete_flagged_complaints():
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=5)
        flagged = Complaint.query.filter(
            Complaint.flagged_at.isnot(None),
            Complaint.flagged_at <= cutoff
        ).all()
        for complaint in flagged:
            # Delete associated votes first
            Vote.query.filter_by(complaint_id=complaint.id).delete()
            # Delete associated image file if present
            if complaint.image_path:
                image_full_path = os.path.join('static', complaint.image_path)
                if os.path.exists(image_full_path):
                    os.remove(image_full_path)
            db.session.delete(complaint)
        if flagged:
            db.session.commit()

# Start the scheduler (only once, not in Flask's reloader child process)
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=auto_delete_flagged_complaints, trigger='interval', hours=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)
