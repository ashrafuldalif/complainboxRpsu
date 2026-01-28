from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
import math
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

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
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
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

# Routes
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
def admin():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('admin.html', complaints=complaints)

@app.route('/admin/complaint/<int:id>')
def view_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    return render_template('view_complaint.html', complaint=complaint)

@app.route('/admin/update_status/<int:id>', methods=['POST'])
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
    return render_template('feed.html', complaints=complaints)

@app.route('/api/complaint/<int:id>/agree', methods=['POST'])
@login_required
def agree_complaint(id):
    try:
        complaint = Complaint.query.get_or_404(id)
        complaint.agree_count += 1
        db.session.commit()
        return jsonify({'success': True, 'agree_count': complaint.agree_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/complaint/<int:id>/disagree', methods=['POST'])
def disagree_complaint(id):
    try:
        complaint = Complaint.query.get_or_404(id)
        complaint.disagree_count += 1
        db.session.commit()
        return jsonify({'success': True, 'disagree_count': complaint.disagree_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
