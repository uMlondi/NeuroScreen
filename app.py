# Standard library imports
import os
from io import BytesIO

# Third-party imports
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, abort
from flask_mail import Mail, Message
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.exc import SQLAlchemyError

# Local imports
from models import db, User, Test, Remedial, save_result, get_filtered_results, export_results_to_csv, create_hardcoded_users
from ld_logic import (
    evaluate_dyslexia,
    evaluate_dyscalculia,
    evaluate_memory,
    evaluate_phonetics,
    evaluate_phonetics_legacy_mcq,
)
from sqlalchemy import or_

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'devkey')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

# Initialize extensions
mail = Mail(app)
db.init_app(app)
migrate = Migrate(app, db)

# Initialize serializer
serializer = URLSafeTimedSerializer(app.secret_key)

DIFFICULTY_LEVELS = ("easy", "medium", "hard")


def _normalize_difficulty(difficulty: str) -> str:
    """Return a sanitized difficulty value or abort if unsupported."""
    normalized = (difficulty or "medium").lower()
    if normalized not in DIFFICULTY_LEVELS:
        abort(404)
    return normalized


def _required_base_tests():
    """Return the canonical set of test categories we require for completion."""
    return ("comprehension", "memory", "phonetics")


def _normalize_test_to_base(test_type):
    """Map stored Result.test_type strings to our base categories."""
    if not test_type:
        return None
    t = str(test_type).lower()
    if t.startswith('comprehension'):
        return 'comprehension'
    if t.startswith('working memory'):
        return 'memory'
    # Our Phonetics assessment currently stores as 'Dyscalculia (...)'
    if t.startswith('dyscalculia') or t.startswith('phonetics'):
        return 'phonetics'
    return None


def _get_completed_base_tests(user):
    """Return a set of base tests the user has completed based on Result rows."""
    try:
        from models import Result
        rows = Result.query.filter_by(email=user.email).all()
        done = set()
        for r in rows:
            base = _normalize_test_to_base(getattr(r, 'test_type', ''))
            if base:
                done.add(base)
        return done
    except Exception:
        return set()


def _get_progress(user):
    """Compute completion progress for required tests."""
    done = _get_completed_base_tests(user)
    total = len(_required_base_tests())
    pct = int(round((len(done) * 100) / total)) if total else 0
    return done, total, pct


def _ensure_test_user():
    """Ensure the current user is logged in and has completed prerequisites."""
    user = db.session.get(User, session.get('user_id'))
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return None, redirect(url_for('login'))

    if not user.completed_get_to_know_you:
        flash('Please complete the "Get to Know You" assessment first.')
        return user, redirect(url_for('landing'))

    return user, None


def _render_level_unavailable(template_name: str, *, difficulty: str, user, **context):
    """Render a placeholder page when a difficulty level is not yet available."""
    payload = {
        'user': user,
        'difficulty': difficulty,
        'difficulties': DIFFICULTY_LEVELS,
        'available': False,
    }
    payload.update(context)
    return render_template(template_name, **payload)

# Login required decorator
def login_required(f):
    """Decorator to require login for protected routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    """Decorator to require admin role for protected routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.')
            return redirect(url_for('login'))

        user = db.session.get(User, session['user_id'])
        if not user or user.role not in ['admin', 'superuser']:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('landing'))

        return f(*args, **kwargs)
    return decorated_function

# Counselor required decorator
def counselor_required(f):
    """Decorator to require counselor or admin role for protected routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.')
            return redirect(url_for('login'))

        user = db.session.get(User, session['user_id'])
        if not user or user.role not in ['counselor', 'admin', 'superuser']:
            flash('Access denied. Counselor or Admin privileges required.')
            return redirect(url_for('landing'))

        return f(*args, **kwargs)
    return decorated_function

def validate_configuration():
    """Validate critical configuration settings."""
    required_configs = [
        ('SECRET_KEY', app.secret_key),
        ('SQLALCHEMY_DATABASE_URI', app.config['SQLALCHEMY_DATABASE_URI'])
    ]

    missing_configs = [key for key, value in required_configs if not value or (key == 'SECRET_KEY' and value == 'devkey')]

    if missing_configs:
        print(f"Warning: Missing or default configuration for: {', '.join(missing_configs)}")
        print("Please set these environment variables for production use.")

def migrate_database():
    """Migrate database schema for new fields."""
    try:
        with app.app_context():
            # Check if new columns exist, if not, add them
            inspector = db.inspect(db.engine)
            if inspector.has_table('user'):
                columns = [col['name'] for col in inspector.get_columns('user')]

                if 'age' not in columns:
                    print("Adding age column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN age INTEGER'))

                if 'gender' not in columns:
                    print("Adding gender column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN gender VARCHAR(20)'))

                if 'course' not in columns:
                    print("Adding course column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN course VARCHAR(100)'))

                if 'year' not in columns:
                    print("Adding year column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN year VARCHAR(20)'))

                # Add Get to Know You response columns
                if 'g2k_learning_style' not in columns:
                    print("Adding g2k_learning_style column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN g2k_learning_style VARCHAR(50)'))

                if 'g2k_diagnosed_difficulties' not in columns:
                    print("Adding g2k_diagnosed_difficulties column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN g2k_diagnosed_difficulties VARCHAR(100)'))

                if 'g2k_age_group' not in columns:
                    print("Adding g2k_age_group column to User table...")
                    db.session.execute(db.text('ALTER TABLE user ADD COLUMN g2k_age_group VARCHAR(20)'))

                db.session.commit()
                print("Database migration completed successfully!")
            else:
                print("User table does not exist yet. Migration will be handled by db.create_all().")
    except Exception as e:
        print(f"Database migration error: {e}")
        db.session.rollback()
        # For SQLite, we might need to recreate the table
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            print("SQLite detected. Migration may require manual intervention.")
            print("Consider deleting the database file to recreate with new schema.")

def initialize_database():
    """Initialize database with comprehensive error handling."""
    try:
        with app.app_context():
            db.create_all()
            migrate_database()
            print("Database initialized successfully!")
    except SQLAlchemyError as e:
        print(f"Database initialization error: {e}")
        # Handle SQLite corruption
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path) and ('malformed' in str(e) or 'corrupt' in str(e)):
                print(f"Detected corrupted database file: {db_path}")
                try:
                    os.remove(db_path)
                    print("Corrupted database removed. Creating fresh database...")
                    with app.app_context():
                        db.create_all()
                        migrate_database()
                    print("Fresh database created successfully!")
                except OSError as os_error:
                    print(f"Failed to remove corrupted database: {os_error}")
                    raise e
            else:
                raise e
        else:
            raise e
    except Exception as e:
        print(f"Unexpected error during database initialization: {e}")
        raise e

# Validate configuration
validate_configuration()

# Initialize database with error handling
initialize_database()

def create_sample_data():
    """Create sample students and assessments if they don't exist."""
    try:
        with app.app_context():
            # Create sample students if none exist
            if not User.query.filter_by(role='student').first():
                sample_students = [
                    {
                        'name': 'John Doe',
                        'email': 'john.doe@example.com',
                        'role': 'student',
                        'age': 20,
                        'gender': 'Male',
                        'course': 'Computer Science',
                        'year': 'Sophomore'
                    },
                    {
                        'name': 'Jane Smith',
                        'email': 'jane.smith@example.com',
                        'role': 'student',
                        'age': 22,
                        'gender': 'Female',
                        'course': 'Psychology',
                        'year': 'Junior'
                    },
                    {
                        'name': 'Bob Johnson',
                        'email': 'bob.johnson@example.com',
                        'role': 'student',
                        'age': 19,
                        'gender': 'Male',
                        'course': 'Engineering',
                        'year': 'Freshman'
                    }
                ]
                for student_data in sample_students:
                    student = User(**student_data)
                    student.set_password('password123')  # Default password for sample students
                    db.session.add(student)
                db.session.commit()
                print("Sample students created successfully!")

            # Create sample assessments if none exist
            if not Test.query.first():
                sample_assessments = [
                    {
                        'name': 'Dyslexia Test',
                        'description': 'Test for dyslexia symptoms',
                        'difficulty_level': 'medium'
                    },
                    {
                        'name': 'Dyscalculia Test',
                        'description': 'Test for dyscalculia symptoms',
                        'difficulty_level': 'medium'
                    },
                    {
                        'name': 'Memory Test',
                        'description': 'Test for memory issues',
                        'difficulty_level': 'easy'
                    }
                ]
                for assessment_data in sample_assessments:
                    assessment = Test(**assessment_data)
                    db.session.add(assessment)
                db.session.commit()
                print("Sample assessments created successfully!")
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.session.rollback()



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            age_str = request.form.get('age', '').strip()
            gender = request.form.get('gender', '').strip()
            course = request.form.get('course', '').strip()
            year = request.form.get('year', '').strip()

            # Input validation
            if not all([name, email, password, age_str, gender, course, year]):
                flash('All fields are required.')
                return redirect(url_for('signup'))

            if len(password) < 6:
                flash('Password must be at least 6 characters long.')
                return redirect(url_for('signup'))

            # Validate age
            try:
                age = int(age_str)
                if age < 1 or age > 120:
                    flash('Please enter a valid age between 1 and 120.')
                    return redirect(url_for('signup'))
            except ValueError:
                flash('Please enter a valid age.')
                return redirect(url_for('signup'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered.')
                return redirect(url_for('signup'))

            user = User(
                name=name,
                email=email,
                role='student',
                age=age,
                gender=gender,
                course=course,
                year=year
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Signup error: {e}")
            flash('An error occurred during signup. Please try again.')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            # Input validation
            if not email or not password:
                flash('Email and password are required.')
                return redirect(url_for('login'))

            # Check hardcoded admin and counselor users
            if email == 'admin@lddetector.com' and password == 'admin123':
                user = User.query.filter_by(email=email).first()
                if not user:
                    # Create admin user if not exists
                    user = User(
                        name='Administrator',
                        email=email,
                        role='admin',
                        age=30,
                        gender='Other',
                        course='N/A',
                        year='N/A'
                    )
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash('Logged in successfully as Admin!')
                return redirect(url_for('admin_dashboard'))

            if email == 'counselor@lddetector.com' and password == 'counselor123':
                user = User.query.filter_by(email=email).first()
                if not user:
                    # Create counselor user if not exists
                    user = User(
                        name='Counselor',
                        email=email,
                        role='counselor',
                        age=28,
                        gender='Other',
                        course='N/A',
                        year='N/A'
                    )
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash('Logged in successfully as Counselor!')
                return redirect(url_for('counselor_dashboard'))

            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash('Logged in successfully!')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password.')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('landing'))

@app.route('/')
def index():
    if session.get('user_id'):
        user = db.session.get(User, session['user_id'])
        if user and not user.completed_get_to_know_you:
            return redirect(url_for('get_to_know_you'))
    return render_template('index.html')

@app.route('/landing', methods=['GET', 'POST'])
@login_required
def landing():
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            # POST not allowed here, redirect to GET
            return redirect(url_for('landing'))

        if not user.completed_get_to_know_you:
            return render_template('get_to_know_you.html', user=user)
        return render_template('tests_landing.html', user=user)
    except Exception as e:
        print(f"Landing page error: {e}")
        session.clear()
        flash('An error occurred. Please log in again.')
        return redirect(url_for('login'))

@app.route('/get-to-know-you', methods=['GET', 'POST'])
@login_required
def get_to_know_you():
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        if user.completed_get_to_know_you:
            return redirect(url_for('index'))

        if request.method == 'POST':
            # Process answers here (save responses and mark as completed)
            user.completed_get_to_know_you = True
            user.g2k_learning_style = request.form.get('learning_style', '').strip()
            user.g2k_diagnosed_difficulties = request.form.get('diagnosed_difficulties', '').strip()
            user.g2k_age_group = request.form.get('age_group', '').strip()
            db.session.commit()
            flash('Assessment completed! You can now access the tests.')
            return redirect(url_for('index'))

        return render_template('get_to_know_you.html', user=user)
    except Exception as e:
        db.session.rollback()
        print(f"Get to know you error: {e}")
        flash('An error occurred. Please try again.')
        return redirect(url_for('landing'))
# Difficulty-aware question sourcing
from comprehension_questions import get_questions_for_difficulty

@app.route('/test/comprehension', defaults={'difficulty': 'medium'}, methods=['GET', 'POST'])
@app.route('/test/comprehension/<difficulty>', methods=['GET', 'POST'])
@login_required
def test_comprehension(difficulty):
    try:
        user, redirect_resp = _ensure_test_user()
        if redirect_resp:
            return redirect_resp

        difficulty = _normalize_difficulty(difficulty)

        test_data = get_questions_for_difficulty(difficulty)
        blocks = test_data["blocks"]

        # Flatten the 15 chosen questions into a lookup dict
        chosen_questions = []
        for block in blocks.values():
            chosen_questions.extend(block["questions"])
        chosen_map = {q["id"]: q for q in chosen_questions}

        if request.method == 'POST':
            score = 0
            total = 0

            for key, value in request.form.items():
                if not key.startswith("q"):
                    continue

                key_suffix = key[1:]
                if not key_suffix.isdigit():
                    continue

                total += 1
                qid = int(key_suffix)
                question = chosen_map.get(qid)
                if question and value == question["answer"]:
                    score += 1

            if total == 0:
                flash('No questions available for this difficulty yet. Please try another level.')
                return redirect(url_for('test_comprehension', difficulty=difficulty))

            message = f"You scored {score}/{total}."
            save_result(
                user.name,
                user.email,
                f"Comprehension ({difficulty.title()})",
                score,
                score < total // 2,
                message
            )

            # Counselors/Admins see inline results; Students are redirected to gated summary
            if user.role in ['admin', 'superuser', 'counselor']:
                return render_template("results.html", result={
                    "type": f"Comprehension ({difficulty.title()})",
                    "score": score,
                    "total": total,
                    "flag": score < total // 2,
                    "message": message
                })
            return redirect(url_for('student_results'))

        # GET: render the comprehension test page
        return render_template(
            "test_comprehension.html",
            test_data=test_data,
            user=user,
            difficulties=DIFFICULTY_LEVELS
        )

    except Exception as e:
        print(f"Comprehension test error: {e}")
        flash("Error during comprehension test. Try again.")
        return redirect(url_for('landing'))


@app.route('/test/dyslexia', defaults={'difficulty': 'medium'}, methods=['GET', 'POST'])
@app.route('/test/dyslexia/<difficulty>', methods=['GET', 'POST'])
@login_required
def test_dyslexia(difficulty):
    try:
        user, redirect_resp = _ensure_test_user()
        if redirect_resp:
            return redirect_resp

        difficulty = _normalize_difficulty(difficulty)
        available = difficulty == 'medium'

        if not available:
            if request.method == 'POST':
                flash('This difficulty level is coming soon. Please select Medium for the current assessment.')
                return redirect(url_for('test_dyslexia', difficulty=difficulty))
            return _render_level_unavailable('test_dyslexia.html', difficulty=difficulty, user=user)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            runtime = (request.form.get('runtime', '') or '').strip()
            answers = [request.form.get(f'q{i}') for i in range(1, 6)]

            if not name or not email:
                flash('Name and email are required.')
                return redirect(url_for('test_dyslexia', difficulty=difficulty))

            if not all(answers):
                flash('Please answer all questions.')
                return redirect(url_for('test_dyslexia', difficulty=difficulty))

            result = evaluate_dyslexia(answers)
            result_payload = dict(result)
            result_payload['type'] = f"{result['type']} ({difficulty.title()})"
            save_result(name, email, result_payload['type'], result['score'], result['flag'], result['message'])
            # Show inline results for staff; gate students
            if user.role in ['admin', 'superuser', 'counselor']:
                return render_template('results.html', result=result_payload)
            return redirect(url_for('student_results'))

        return render_template(
            'test_dyslexia.html',
            user=user,
            difficulty=difficulty,
            difficulties=DIFFICULTY_LEVELS,
            available=True
        )
    except Exception as e:
        print(f"Dyslexia test error: {e}")
        flash('An error occurred during the test. Please try again.')
        return redirect(url_for('landing'))

@app.route('/test/dyscalculia', defaults={'difficulty': 'medium'}, methods=['GET', 'POST'])
@app.route('/test/dyscalculia/<difficulty>', methods=['GET', 'POST'])
@login_required
def test_dyscalculia(difficulty):
    try:
        user, redirect_resp = _ensure_test_user()
        if redirect_resp:
            return redirect_resp

        difficulty = _normalize_difficulty(difficulty)
        available = difficulty == 'medium'

        if not available:
            if request.method == 'POST':
                flash('This difficulty level is coming soon. Please select Medium for the current assessment.')
                return redirect(url_for('test_dyscalculia', difficulty=difficulty))
            return _render_level_unavailable('test_dyscalculia.html', difficulty=difficulty, user=user)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            answers = request.form.getlist('answer')
            targets = request.form.getlist('target')

            if not name or not email:
                flash('Name and email are required.')
                return redirect(url_for('test_dyscalculia', difficulty=difficulty))

            if not answers or not targets or len(answers) != len(targets) or not all((a or '').strip() for a in answers):
                flash('Please complete all items before submitting.')
                return redirect(url_for('test_dyscalculia', difficulty=difficulty))

            result = evaluate_dyscalculia(answers, targets)
            result_payload = dict(result)
            result_payload['type'] = f"{result['type']} ({difficulty.title()})"
            save_result(name, email, result_payload['type'], result['score'], result['flag'], result['message'])
            if user.role in ['admin', 'superuser', 'counselor']:
                return render_template('results.html', result=result_payload)
            return redirect(url_for('student_results'))

        return render_template(
            'test_dyscalculia.html',
            user=user,
            difficulty=difficulty,
            difficulties=DIFFICULTY_LEVELS,
            available=True
        )
    except Exception as e:
        print(f"Dyscalculia test error: {e}")
        flash('An error occurred during the test. Please try again.')
        return redirect(url_for('landing'))

@app.route('/test/memory', defaults={'difficulty': 'medium'}, methods=['GET', 'POST'])
@app.route('/test/memory/<difficulty>', methods=['GET', 'POST'])
@login_required
def test_memory(difficulty):
    try:
        user, redirect_resp = _ensure_test_user()
        if redirect_resp:
            return redirect_resp

        difficulty = _normalize_difficulty(difficulty)
        available = difficulty == 'medium'

        if not available:
            if request.method == 'POST':
                flash('This difficulty level is coming soon. Please select Medium for the current assessment.')
                return redirect(url_for('test_memory', difficulty=difficulty))
            return _render_level_unavailable('test_memory.html', difficulty=difficulty, user=user)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            answers = request.form.getlist('recall')
            targets = request.form.getlist('target')
            runtime = (request.form.get('runtime', '') or '').strip()

            if not name or not email:
                flash('Name and email are required.')
                return redirect(url_for('test_memory', difficulty=difficulty))

            if not answers or not targets:
                flash('Please provide recall answers.')
                return redirect(url_for('test_memory', difficulty=difficulty))

            result = evaluate_memory(answers, targets)
            result_payload = dict(result)
            result_payload['type'] = f"{result['type']} ({difficulty.title()})"
            # Append runtime if provided
            try:
                if runtime:
                    secs = int(float(runtime))
                    result_payload['message'] = f"{result_payload.get('message','')} Time taken: {secs}s"
            except Exception:
                pass
            save_result(name, email, result_payload['type'], result_payload['score'], result_payload['flag'], result_payload['message'])
            if user.role in ['admin', 'superuser', 'counselor']:
                return render_template('results.html', result=result_payload)
            return redirect(url_for('student_results'))

        return render_template(
            'test_memory.html',
            user=user,
            difficulty=difficulty,
            difficulties=DIFFICULTY_LEVELS,
            available=True
        )
    except Exception as e:
        print(f"Memory test error: {e}")
        flash('An error occurred during the test. Please try again.')
        return redirect(url_for('landing'))

@app.route('/test/phonetics', defaults={'difficulty': 'medium'}, methods=['GET', 'POST'])
@app.route('/test/phonetics/<difficulty>', methods=['GET', 'POST'])
@login_required
def test_phonetics(difficulty):
    try:
        user, redirect_resp = _ensure_test_user()
        if redirect_resp:
            return redirect_resp

        difficulty = _normalize_difficulty(difficulty)
        available = difficulty == 'medium'

        if not available:
            if request.method == 'POST':
                flash('This difficulty level is coming soon. Please select Medium for the current assessment.')
                return redirect(url_for('test_phonetics', difficulty=difficulty))
            return _render_level_unavailable('test_phonetics_spelling.html', difficulty=difficulty, user=user)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()

            if not name or not email:
                flash('Name and email are required.')
                return redirect(url_for('test_phonetics', difficulty=difficulty))

            # New typed inputs
            spells = request.form.getlist('spell')
            targets = request.form.getlist('target')
            levels = request.form.getlist('level')

            result = None
            if spells and targets:
                result = evaluate_phonetics(spells, targets, levels)
            else:
                # Legacy 5-item MCQ fallback (e.g., q1..q5)
                legacy_answers = [request.form.get(f'q{i}') for i in range(1, 6)]
                if any(legacy_answers):
                    result = evaluate_phonetics_legacy_mcq(legacy_answers)
                else:
                    flash('Please complete all items before submitting.')
                    return redirect(url_for('test_phonetics', difficulty=difficulty))

            result_payload = dict(result)
            result_payload['type'] = f"Phonetics ({difficulty.title()})"
            # Append runtime if provided
            try:
                if runtime:
                    secs = int(float(runtime))
                    result_payload['message'] = f"{result_payload.get('message','')} Time taken: {secs}s"
            except Exception:
                pass
            save_result(name, email, result_payload['type'], result_payload.get('score', 0), result_payload.get('flag', False), result_payload.get('message', ''))
            if user.role in ['admin', 'superuser', 'counselor']:
                return render_template('results.html', result=result_payload)
            return redirect(url_for('student_results'))

        return render_template(
            'test_phonetics_spelling.html',
            user=user,
            difficulty=difficulty,
            difficulties=DIFFICULTY_LEVELS,
            available=True
        )
    except Exception as e:
        print(f"Phonetics test error: {e}")
        flash('An error occurred during the test. Please try again.')
        return redirect(url_for('landing'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()

            if not email:
                flash('Please enter your email address.')
                return redirect(url_for('forgot_password'))

            user = User.query.filter_by(email=email).first()
            if user:
                token = serializer.dumps(email, salt='password-reset-salt')
                reset_url = url_for('reset_password', token=token, _external=True)

                # Check if mail server is configured
                if app.config.get('MAIL_USERNAME'):
                    msg = Message(
                        'Password Reset Request - LD Detector',
                        recipients=[email]
                    )
                    msg.body = f'''Hello {user.name},

You have requested to reset your password for your LD Detector account.

Please click the following link to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you did not request this password reset, please ignore this email.

Best regards,
LD Detector Team
'''
                    mail.send(msg)
                    flash('Password reset email sent. Please check your inbox (and spam folder).')
                else:
                    # For development/demo purposes, show the reset link
                    flash(f'Development mode: Reset link - {reset_url}')
            else:
                # Don't reveal if email exists or not for security
                flash('If an account with that email exists, a password reset link has been sent.')

            return redirect(url_for('login'))
        except Exception as e:
            print(f"Forgot password error: {e}")
            flash('An error occurred. Please try again.')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/test/flash_cards', defaults={'difficulty': 'medium'}, methods=['GET', 'POST'])
@app.route('/test/flash_cards/<difficulty>', methods=['GET', 'POST'])
@login_required
def test_flash_cards(difficulty):
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        if not user.completed_get_to_know_you:
            flash('Please complete the "Get to Know You" assessment first.')
            return redirect(url_for('landing'))

        difficulty = (difficulty or 'medium').lower()
        if difficulty not in DIFFICULTY_LEVELS:
            abort(404)

        available = difficulty == 'medium'

        if not available:
            if request.method == 'POST':
                flash('This difficulty level is coming soon. Please select Medium for the current assessment.')
                return redirect(url_for('test_flash_cards', difficulty=difficulty))
            return render_template('test_flash_cards.html', difficulty=difficulty, difficulties=DIFFICULTY_LEVELS, available=False)

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            answers = [request.form.get(f'q{i}') for i in range(1,6)]

            # Validate inputs
            if not name or not email:
                flash('Name and email are required.')
                return redirect(url_for('test_flash_cards', difficulty=difficulty))

            if not all(answers):
                flash('Please answer all questions.')
                return redirect(url_for('test_flash_cards', difficulty=difficulty))

            # Simple evaluation for flash cards (count correct answers)
            correct_answers = ['cat', 'apple', 'book', 'house', 'sun']
            score = sum(1 for user_ans, correct_ans in zip(answers, correct_answers)
                       if user_ans and user_ans.lower().strip() == correct_ans.lower())

            flag = score < 3  # Flag if less than 3 correct
            message = f"You correctly identified {score} out of 5 flash card items."

            save_result(name, email, f'Flash Cards ({difficulty.title()})', score, flag, message)
            result = {
                'type': f'Flash Cards ({difficulty.title()})',
                'score': score,
                'flag': flag,
                'message': message
            }
            return render_template('results.html', result=result)

        return render_template('test_flash_cards.html', difficulty=difficulty, difficulties=DIFFICULTY_LEVELS, available=True)
    except Exception as e:
        print(f"Flash cards test error: {e}")
        flash('An error occurred during the test. Please try again.')
        return redirect(url_for('landing'))

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception as e:
        print(f"Token validation error: {e}")
        flash('The password reset link is invalid or has expired. Please request a new one.')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        try:
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not password:
                flash('Please enter a new password.')
                return redirect(url_for('reset_password', token=token))

            if len(password) < 6:
                flash('Password must be at least 6 characters long.')
                return redirect(url_for('reset_password', token=token))

            if password != confirm_password:
                flash('Passwords do not match.')
                return redirect(url_for('reset_password', token=token))

            user.set_password(password)
            db.session.commit()
            flash('Your password has been updated successfully. Please log in with your new password.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Password reset error: {e}")
            flash('An error occurred while updating your password. Please try again.')
            return redirect(url_for('reset_password', token=token))

    return render_template('reset_password.html')

@app.route('/admin')
@counselor_required
def admin_dashboard():
    try:
        user = db.session.get(User, session['user_id'])
        # Filters: email, test_type
        email = request.args.get('email', '').strip()
        test_type = request.args.get('test_type', '').strip()
        results = get_filtered_results(email=email or None, test_type=test_type or None)
        return render_template('admin_dashboard.html', results=results, email=email, test_type=test_type, user=user)
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('An error occurred loading the admin dashboard.')
        return redirect(url_for('landing'))

@app.route('/assessments')
@login_required
def assessments():
    try:
        user = db.session.get(User, session['user_id'])
        completed_set, total_tests, progress_pct = _get_progress(user)
        completed_count = len(completed_set)
        return render_template(
            'assessments.html',
            user=user,
            completed_tests=completed_set,
            completed_count=completed_count,
            total_tests=total_tests,
            progress_pct=progress_pct
        )
    except Exception as e:
        print(f"Assessments page error: {e}")
        flash('An error occurred loading the assessments page.')
        return redirect(url_for('index'))

@app.route('/results')
@login_required
def student_results():
    """Aggregate results for the current user. Students are gated until all tests complete."""
    try:
        user = db.session.get(User, session['user_id'])
        completed_set, total_tests, progress_pct = _get_progress(user)

        # Gate students until all required tests are done
        if user.role not in ['admin', 'superuser', 'counselor'] and len(completed_set) < total_tests:
            flash('Please complete all tests to view results')
            return redirect(url_for('assessments'))

        # Fetch the latest result per base category
        from models import Result
        def latest_like(prefix):
            return (Result.query
                    .filter(Result.email == user.email, Result.test_type.ilike(f"{prefix}%"))
                    .order_by(Result.timestamp.desc())
                    .first())

        comprehension_row = latest_like('Comprehension (')
        memory_row = latest_like('Working Memory (')
        # Support legacy Dyscalculia label and new Phonetics label
        from models import Result
        phonetics_row = (Result.query
                         .filter(
                             Result.email == user.email,
                             or_(
                                 Result.test_type.ilike('Dyscalculia (%'),
                                 Result.test_type.ilike('Phonetics (%')
                             )
                         )
                         .order_by(Result.timestamp.desc())
                         .first())

        # Attach totals so summary can show correct denominators
        # Comprehension: try parse from saved message 'You scored X/Y.'; fallback to question bank size
        if comprehension_row and getattr(comprehension_row, 'test_type', None):
            try:
                msg = (getattr(comprehension_row, 'message', '') or '').strip()
                total_from_msg = None
                slash = msg.rfind('/')
                if slash != -1:
                    # read digits after '/'
                    j = slash + 1
                    digits = ''
                    while j < len(msg) and msg[j].isdigit():
                        digits += msg[j]
                        j += 1
                    if digits:
                        total_from_msg = int(digits)
                if total_from_msg:
                    setattr(comprehension_row, 'total', total_from_msg)
                else:
                    # Fallback: infer from question bank by difficulty label
                    label = comprehension_row.test_type
                    diff = label[label.find('(')+1:label.find(')')].strip().lower()
                    from comprehension_questions import get_questions_for_difficulty
                    td = get_questions_for_difficulty(diff)
                    blocks = td.get('blocks', {})
                    comp_total = 0
                    for b in blocks.values():
                        comp_total += len(b.get('questions', []))
                    setattr(comprehension_row, 'total', comp_total if comp_total else 5)
            except Exception:
                pass
        if memory_row:
            try:
                setattr(memory_row, 'total', 12)
            except Exception:
                pass
        if phonetics_row:
            try:
                setattr(phonetics_row, 'total', 9)
            except Exception:
                pass

        summary_results = [r for r in (comprehension_row, memory_row, phonetics_row) if r]

        # Students should not see timing; sanitize 'Time taken: Ns' from messages
        try:
            if user.role not in ['admin', 'superuser', 'counselor']:
                for r in summary_results:
                    msg = (getattr(r, 'message', '') or '')
                    cut = msg.find('Time taken:')
                    if cut != -1:
                        setattr(r, 'message', msg[:cut].strip())
        except Exception:
            pass

        return render_template(
            'results.html',
            user=user,
            summary_results=summary_results,
            progress_pct=progress_pct,
            completed_count=len(completed_set),
            total_tests=total_tests
        )
    except Exception as e:
        print(f"Student results error: {e}")
        flash('An error occurred loading your results.')
        return redirect(url_for('assessments'))

@app.route('/programs')
@login_required
def programs():
    """Personalized programs page, unlocked after completing all base tests for students."""
    try:
        user = db.session.get(User, session['user_id'])
        completed_set, total_tests, progress_pct = _get_progress(user)

        # Gate students until all required tests are done; staff bypass
        if user.role not in ['admin', 'superuser', 'counselor'] and len(completed_set) < total_tests:
            flash('Please complete all tests to unlock personalized programs')
            return redirect(url_for('assessments'))

        from models import Result
        def latest_like(prefix):
            return (Result.query
                    .filter(Result.email == user.email, Result.test_type.ilike(f"{prefix}%"))
                    .order_by(Result.timestamp.desc())
                    .first())

        comprehension_row = latest_like('Comprehension (')
        memory_row = latest_like('Working Memory (')
        # Support legacy Dyscalculia label and new Phonetics label
        phonetics_row = (Result.query
                         .filter(
                             Result.email == user.email,
                             or_(
                                 Result.test_type.ilike('Dyscalculia (%'),
                                 Result.test_type.ilike('Phonetics (%')
                             )
                         )
                         .order_by(Result.timestamp.desc())
                         .first())

        # Attach totals
        if comprehension_row and getattr(comprehension_row, 'test_type', None):
            try:
                label = comprehension_row.test_type
                diff = label[label.find('(')+1:label.find(')')].strip().lower()
                from comprehension_questions import get_questions_for_difficulty
                td = get_questions_for_difficulty(diff)
                blocks = td.get('blocks', {})
                comp_total = 0
                for b in blocks.values():
                    comp_total += len(b.get('questions', []))
                setattr(comprehension_row, 'total', comp_total if comp_total else 5)
            except Exception:
                pass
        if memory_row:
            try:
                setattr(memory_row, 'total', 12)
            except Exception:
                pass
        if phonetics_row:
            try:
                setattr(phonetics_row, 'total', 9)
            except Exception:
                pass

        # Students should not see timing on programs; sanitize 'Time taken: Ns'
        try:
            if user.role not in ['admin', 'superuser', 'counselor']:
                for r in (comprehension_row, memory_row, phonetics_row):
                    if not r:
                        continue
                    msg = (getattr(r, 'message', '') or '')
                    cut = msg.find('Time taken:')
                    if cut != -1:
                        setattr(r, 'message', msg[:cut].strip())
        except Exception:
            pass

        return render_template(
            'programs.html',
            user=user,
            comprehension=comprehension_row,
            memory=memory_row,
            phonetics=phonetics_row,
            progress_pct=progress_pct,
            completed_count=len(completed_set),
            total_tests=total_tests,
            phonetics_max=9
        )
    except Exception as e:
        print(f"Programs page error: {e}")
        flash('An error occurred loading your programs.')
        return redirect(url_for('assessments'))
@app.route('/counselor')
@counselor_required
def counselor_dashboard():
    try:
        user = db.session.get(User, session['user_id'])

        # Get all students
        search_query = request.args.get('search', '').strip().lower()
        if search_query:
            students = User.query.filter(
                User.role == 'student',
                (User.name.ilike(f'%{search_query}%')) | (User.email.ilike(f'%{search_query}%'))
            ).all()
        else:
            students = User.query.filter_by(role='student').all()

        # Get all programs (remedials) and assessments (tests)
        programs = Remedial.query.all()
        assessments = Test.query.all()

        return render_template('counselor_dashboard.html', students=students, programs=programs, assessments=assessments, user=user, search_query=search_query)
    except Exception as e:
        print(f"Counselor dashboard error: {e}")
        flash('An error occurred loading the counselor dashboard.')
        return redirect(url_for('landing'))

@app.route('/counselor/results/<int:student_id>')
@counselor_required
def view_student_results(student_id):
    try:
        from models import get_student_results
        results = get_student_results(student_id)
        student = User.query.get_or_404(student_id)
        return render_template('counselor_results.html', results=results, student=student)
    except Exception as e:
        print(f"View student results error: {e}")
        flash('An error occurred loading student results.')
        return redirect(url_for('counselor_dashboard'))

@app.route('/counselor/generate_graph')
@counselor_required
def generate_graph():
    try:
        from models import get_results_aggregates
        aggregates = get_results_aggregates()
        return {'aggregates': aggregates}
    except Exception as e:
        print(f"Generate graph error: {e}")
        return {'error': 'An error occurred generating graph data.'}, 500

@app.route('/counselor/add_program', methods=['POST'])
@counselor_required
def add_program():
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        test_id = request.form.get('test_id', '').strip()

        if not all([name, description, test_id]):
            flash('All fields are required.')
            return redirect(url_for('counselor_dashboard'))

        # Validate test_id exists
        test = Test.query.get(int(test_id))
        if not test:
            flash('Invalid test selected.')
            return redirect(url_for('counselor_dashboard'))

        remedial = Remedial(
            test_id=int(test_id),
            name=name,
            description=description
        )
        db.session.add(remedial)
        db.session.commit()
        flash('Program added successfully!')
        return redirect(url_for('counselor_dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Add program error: {e}")
        flash('An error occurred adding the program.')
        return redirect(url_for('counselor_dashboard'))

@app.route('/counselor/delete_program/<int:program_id>', methods=['POST'])
@counselor_required
def delete_program(program_id):
    try:
        remedial = Remedial.query.get_or_404(program_id)
        db.session.delete(remedial)
        db.session.commit()
        flash('Program deleted successfully!')
        return redirect(url_for('counselor_dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Delete program error: {e}")
        flash('An error occurred deleting the program.')
        return redirect(url_for('counselor_dashboard'))

@app.route('/counselor/add_assessment', methods=['POST'])
@counselor_required
def add_assessment():
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        difficulty_level = request.form.get('difficulty_level', 'medium').strip()

        if not all([name, description]):
            flash('Name and description are required.')
            return redirect(url_for('counselor_dashboard'))

        if difficulty_level not in ['easy', 'medium', 'hard']:
            difficulty_level = 'medium'

        test = Test(
            name=name,
            description=description,
            difficulty_level=difficulty_level
        )
        db.session.add(test)
        db.session.commit()
        flash('Assessment added successfully!')
        return redirect(url_for('counselor_dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Add assessment error: {e}")
        flash('An error occurred adding the assessment.')
        return redirect(url_for('counselor_dashboard'))

@app.route('/counselor/delete_assessment/<int:assessment_id>', methods=['POST'])
@counselor_required
def delete_assessment(assessment_id):
    try:
        test = Test.query.get_or_404(assessment_id)
        # Check if there are related remedials
        if Remedial.query.filter_by(test_id=assessment_id).first():
            flash('Cannot delete assessment with associated programs. Delete programs first.')
            return redirect(url_for('counselor_dashboard'))

        db.session.delete(test)
        db.session.commit()
        flash('Assessment deleted successfully!')
        return redirect(url_for('counselor_dashboard'))
    except Exception as e:
        db.session.rollback()
        print(f"Delete assessment error: {e}")
        flash('An error occurred deleting the assessment.')
        return redirect(url_for('counselor_dashboard'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        # Get user's test results for progress tracking
        from models import Result
        user_results = Result.query.filter_by(email=user.email).order_by(Result.timestamp.desc()).limit(10).all()

        return render_template('student_dashboard.html', user=user, results=user_results)
    except Exception as e:
        print(f"Student dashboard error: {e}")
        flash('An error occurred loading the dashboard.')
        return redirect(url_for('landing'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            # Update profile information
            name = request.form.get('name', '').strip()
            age_str = request.form.get('age', '').strip()
            gender = request.form.get('gender', '').strip()
            course = request.form.get('course', '').strip()
            year = request.form.get('year', '').strip()

            # Validation
            if not all([name, age_str, gender, course, year]):
                flash('All fields are required.')
                return redirect(url_for('profile'))

            try:
                age = int(age_str)
                if age < 1 or age > 120:
                    flash('Please enter a valid age between 1 and 120.')
                    return redirect(url_for('profile'))
            except ValueError:
                flash('Please enter a valid age.')
                return redirect(url_for('profile'))

            # Update user
            user.name = name
            user.age = age
            user.gender = gender
            user.course = course
            user.year = year

            db.session.commit()
            session['user_name'] = name  # Update session
            flash('Profile updated successfully!')
            return redirect(url_for('profile'))

        return render_template('profile.html', user=user)
    except Exception as e:
        db.session.rollback()
        print(f"Profile error: {e}")
        flash('An error occurred updating your profile.')
        return redirect(url_for('profile'))

@app.route('/admin/export')
@counselor_required
def admin_export():
    try:
        email = request.args.get('email', '').strip()
        test_type = request.args.get('test_type', '').strip()
        filename = export_results_to_csv(email=email or None, test_type=test_type or None)
        return send_file(filename, as_attachment=True)
    except Exception as e:
        print(f"Admin export error: {e}")
        flash('An error occurred during export.')
        return redirect(url_for('admin'))

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors gracefully."""
    db.session.rollback()
    print(f"Internal server error: {error}")
    flash('An unexpected error occurred. Please try again.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    try:
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            # Handle settings updates (notifications, theme preferences, etc.)
            email_notifications = request.form.get('email_notifications') == 'on'
            theme_preference = request.form.get('theme', 'light')

            # For now, we'll store these in session (could be extended to database)
            session['email_notifications'] = email_notifications
            session['theme_preference'] = theme_preference

            flash('Settings updated successfully!')
            return redirect(url_for('settings'))

        return render_template('settings.html', user=user)
    except Exception as e:
        print(f"Settings error: {e}")
        flash('An error occurred updating settings.')
        return redirect(url_for('settings'))

@app.route('/results/<int:result_id>')
@login_required
def view_result(result_id):
    try:
        from models import Result
        result = Result.query.get_or_404(result_id)

        # Check if user owns this result or is admin
        user = db.session.get(User, session['user_id'])
        if not user:
            session.clear()
            flash('Session expired. Please log in again.')
            return redirect(url_for('login'))

        if result.email != user.email and user.role not in ['admin', 'superuser']:
            flash('Access denied.')
            return redirect(url_for('landing'))

        return render_template('result_detail.html', result=result)
    except Exception as e:
        print(f"View result error: {e}")
        flash('An error occurred loading the result.')
        return redirect(url_for('landing'))

@app.route('/help')
def help_page():
    """Help and FAQ page."""
    return render_template('help.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page."""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()

            if not all([name, email, subject, message]):
                flash('All fields are required.')
                return redirect(url_for('contact'))

            # For now, just flash a success message
            # In production, you'd send an email or save to database
            flash('Thank you for your message. We will get back to you soon!')
            return redirect(url_for('contact'))
        except Exception as e:
            print(f"Contact form error: {e}")
            flash('An error occurred sending your message. Please try again.')
            return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
