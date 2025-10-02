from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import csv
from sqlalchemy.orm import validates
from sqlalchemy.sql import expression

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(
        db.Enum('admin', 'counselor', 'student', name='user_roles'),
        nullable=False,
        default='student',
        server_default='student'
    )
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=expression.true())
    completed_get_to_know_you = db.Column(db.Boolean, default=False)

    # New fields for student info
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)

    # Get to Know You responses
    g2k_learning_style = db.Column(db.String(50), nullable=True)
    g2k_diagnosed_difficulties = db.Column(db.String(100), nullable=True)
    g2k_age_group = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    programs_created = db.relationship('Program', backref='creator', lazy='dynamic')
    reviews = db.relationship('Review', backref='student', lazy='dynamic', foreign_keys='Review.student_id')
    counselor_assignments = db.relationship(
        'CounselorStudent',
        backref='counselor',
        lazy='dynamic',
        foreign_keys='CounselorStudent.counselor_id'
    )
    student_assignments = db.relationship(
        'CounselorStudent',
        backref='student',
        lazy='dynamic',
        foreign_keys='CounselorStudent.student_id'
    )
    reset_requests = db.relationship('PasswordResetRequest', backref='user', lazy='dynamic')


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    reviews = db.relationship('Review', backref='program', lazy='dynamic')

    @validates('created_by')
    def validate_created_by(self, key, value):
        user = User.query.get(value) if value is not None else None
        if user is None:
            raise ValueError('Program creator must be a valid user.')
        if user.role != 'counselor':
            raise ValueError('Only counselors can create programs.')
        return value


class PasswordResetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True)
    status = db.Column(
        db.Enum('pending', 'approved', 'denied', 'completed', name='password_reset_status'),
        nullable=False,
        default='pending',
        server_default='pending'
    )
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    feedback = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @validates('student_id')
    def validate_student(self, key, value):
        user = User.query.get(value) if value is not None else None
        if user is None:
            raise ValueError('Review must reference a valid student.')
        if user.role != 'student':
            raise ValueError('Only students can submit reviews.')
        return value

    @validates('rating')
    def validate_rating(self, key, value):
        if value is None:
            raise ValueError('Rating is required.')
        if not (1 <= int(value) <= 5):
            raise ValueError('Rating must be between 1 and 5.')
        return value


class CounselorStudent(db.Model):
    __tablename__ = 'counselor_student'
    __table_args__ = (
        db.UniqueConstraint('counselor_id', 'student_id', name='uq_counselor_student_pair'),
    )

    id = db.Column(db.Integer, primary_key=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @validates('counselor_id')
    def validate_counselor(self, key, value):
        user = User.query.get(value) if value is not None else None
        if user is None:
            raise ValueError('Counselor assignment must reference a valid counselor.')
        if user.role != 'counselor':
            raise ValueError('Counselor assignments require counselor role users.')
        return value

    @validates('student_id')
    def validate_student(self, key, value):
        user = User.query.get(value) if value is not None else None
        if user is None:
            raise ValueError('Counselor assignment must reference a valid student.')
        if user.role != 'student':
            raise ValueError('Counselor assignments require student role users.')
        return value
    
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    test_type = db.Column(db.String(50))
    score = db.Column(db.Integer)
    flag = db.Column(db.Boolean)
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., 'Comprehension', 'Memory Test', etc.
    description = db.Column(db.Text, nullable=True)
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Remedial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)  # Text or URL to resources
    function = db.Column(db.Text, nullable=True)  # Description of remedial purpose
    difficulty_level = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User_Test_Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=True)
    flag = db.Column(db.Boolean, default=False)  # Indicates dyslexia
    message = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # In seconds

class User_Remedial_Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    remedial_id = db.Column(db.Integer, db.ForeignKey('remedial.id'), nullable=False)
    status = db.Column(db.String(20), default='started')  # started, in_progress, completed
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Counselor feedback

def save_result(name, email, test_type, score, flag, message):
    r = Result(name=name, email=email, test_type=test_type, score=score, flag=bool(flag), message=message)
    db.session.add(r)
    db.session.commit()

def get_filtered_results(email=None, test_type=None):
    q = Result.query.order_by(Result.timestamp.desc())
    if email:
        q = q.filter(Result.email.ilike(f"%{email}%"))
    if test_type:
        q = q.filter(Result.test_type == test_type)
    return q.all()

def export_results_to_csv(email=None, test_type=None):
    results = get_filtered_results(email=email, test_type=test_type)
    filename = f"exported_results_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    # write to file in project folder
    path = filename
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Email', 'Test Type', 'Score', 'Flag', 'Message', 'Timestamp'])
        for r in results:
            writer.writerow([r.name, r.email, r.test_type, r.score, 'Yes' if r.flag else 'No', r.message, r.timestamp])
    return path

def save_attempt(user_id, test_id, score, flag, message, duration=None):
    attempt = User_Test_Attempt(
        user_id=user_id,
        test_id=test_id,
        score=score,
        flag=flag,
        message=message,
        duration=duration
    )
    db.session.add(attempt)
    db.session.commit()

def get_user_attempts(user_id=None, test_id=None):
    q = User_Test_Attempt.query.order_by(User_Test_Attempt.attempt_date.desc())
    if user_id:
        q = q.filter_by(user_id=user_id)
    if test_id:
        q = q.filter_by(test_id=test_id)
    return q.all()

def save_remedial_progress(user_id, remedial_id, status, progress_percentage, notes=None):
    progress = User_Remedial_Progress.query.filter_by(user_id=user_id, remedial_id=remedial_id).first()
    if not progress:
        progress = User_Remedial_Progress(user_id=user_id, remedial_id=remedial_id)
        db.session.add(progress)
    progress.status = status
    progress.progress_percentage = progress_percentage
    if notes:
        progress.notes = notes
    if status == 'completed':
        progress.completed_at = datetime.utcnow()
    db.session.commit()

def get_user_remedial_progress(user_id=None, remedial_id=None):
    q = User_Remedial_Progress.query.order_by(User_Remedial_Progress.started_at.desc())
    if user_id:
        q = q.filter_by(user_id=user_id)
    if remedial_id:
        q = q.filter_by(remedial_id=remedial_id)
    return q.all()

def get_student_results(student_id):
    """Get all results for a specific student by user ID."""
    return Result.query.filter_by(email=User.query.get(student_id).email).order_by(Result.timestamp.desc()).all()

def get_all_students():
    """Get all users with role 'student'."""
    return User.query.filter_by(role='student').all()

def get_programs():
    """Get all remedial programs."""
    return Remedial.query.all()

def get_results_aggregates():
    """Get aggregated data for graphs: average scores by test type, flagged counts, etc."""
    from sqlalchemy import func
    results = db.session.query(
        Result.test_type,
        func.avg(Result.score).label('avg_score'),
        func.count(Result.id).label('total_results'),
        func.sum(func.case((Result.flag == True, 1), else_=0)).label('flagged_count')
    ).group_by(Result.test_type).all()
    return results

def create_sample_tests_and_remedials():
    """Create sample tests and remedials if they don't exist."""
    # Tests
    tests_data = [
        {'name': 'Comprehension', 'description': 'Reading comprehension test', 'difficulty_level': 'medium'},
        {'name': 'Memory Test', 'description': 'Short-term memory recall test', 'difficulty_level': 'medium'},
        {'name': 'Phonetics', 'description': 'Sound-letter mapping test', 'difficulty_level': 'easy'},
        {'name': 'Flash Card Test', 'description': 'Quick recognition and spelling test', 'difficulty_level': 'hard'}
    ]
    for data in tests_data:
        if not Test.query.filter_by(name=data['name']).first():
            test = Test(**data)
            db.session.add(test)
    db.session.commit()

    # Remedials (assuming tests are created)
    comprehension = Test.query.filter_by(name='Comprehension').first()
    memory = Test.query.filter_by(name='Memory Test').first()
    phonetics = Test.query.filter_by(name='Phonetics').first()
    flashcards = Test.query.filter_by(name='Flash Card Test').first()

    remedials_data = [
        {'test_id': comprehension.id if comprehension else 1, 'name': 'Guided Reading Exercise', 'description': 'Interactive passages with questions', 'function': 'Build reading comprehension through guided exercises'},
        {'test_id': memory.id if memory else 2, 'name': 'Memory Recall Game', 'description': 'Word sequence recall drills', 'function': 'Strengthen short-term memory with games'},
        {'test_id': phonetics.id if phonetics else 3, 'name': 'Sound Mapping Drill', 'description': 'Pronunciation and letter-sound practice', 'function': 'Enhance phonetic awareness'},
        {'test_id': flashcards.id if flashcards else 4, 'name': 'Spelling Flash Cards', 'description': 'Timed word recognition', 'function': 'Improve spelling and quick recognition'}
    ]
    for data in remedials_data:
        if not Remedial.query.filter_by(name=data['name']).first():
            remedial = Remedial(**data)
            db.session.add(remedial)
    db.session.commit()

def create_hardcoded_users():
    """Create hardcoded admin and counselor users if they don't exist."""
    # Admin user
    admin = User.query.filter_by(email='admin@lddetector.com').first()
    if not admin:
        admin = User(
            name='Administrator',
            email='admin@lddetector.com',
            role='admin',
            age=30,
            gender='Other',
            course='N/A',
            year='N/A'
        )
        admin.set_password('admin123')  # Hardcoded password
        db.session.add(admin)

    # Counselor user
    counselor = User.query.filter_by(email='counselor@lddetector.com').first()
    if not counselor:
        counselor = User(
            name='Counselor',
            email='counselor@lddetector.com',
            role='counselor',
            age=28,
            gender='Other',
            course='N/A',
            year='N/A'
        )
        counselor.set_password('counselor123')  # Hardcoded password
        db.session.add(counselor)

    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
