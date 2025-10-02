import pytest
from app import app, db, User, Test, Remedial
from flask import session
import tempfile
import os

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test_secret_key'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()

            # Clear existing data to avoid unique constraint issues
            db.session.query(Remedial).delete()
            db.session.query(Test).delete()
            db.session.query(User).delete()
            db.session.commit()

            # Create test users
            counselor = User(
                name='Test Counselor',
                email='counselor@test.com',
                role='counselor',
                age=30,
                gender='Other',
                course='N/A',
                year='N/A'
            )
            counselor.set_password('password123')
            db.session.add(counselor)

            student = User(
                name='Test Student',
                email='student@test.com',
                role='student',
                age=20,
                gender='Other',
                course='Computer Science',
                year='2023'
            )
            student.set_password('password123')
            db.session.add(student)

            # Create test assessment
            test = Test(
                name='Test Assessment',
                description='A test assessment',
                difficulty_level='medium'
            )
            db.session.add(test)
            db.session.commit()

            yield client

def login_counselor(client):
    """Helper function to log in as counselor."""
    response = client.post('/login', data={
        'email': 'counselor@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    return response

def login_student(client):
    """Helper function to log in as student."""
    response = client.post('/login', data={
        'email': 'student@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    return response

def test_add_program_success(client):
    """Test adding a program successfully."""
    login_counselor(client)

    response = client.post('/counselor/add_program', data={
        'name': 'Test Program',
        'description': 'A test remedial program',
        'test_id': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check that we were redirected to the counselor dashboard
    assert b'Counselor Dashboard' in response.data

    # Verify program was added to database
    with app.app_context():
        program = Remedial.query.filter_by(name='Test Program').first()
        assert program is not None
        assert program.description == 'A test remedial program'
        assert program.test_id == 1

def test_add_program_missing_fields(client):
    """Test adding a program with missing fields."""
    login_counselor(client)

    # Count programs before attempt
    with app.app_context():
        initial_count = Remedial.query.count()

    response = client.post('/counselor/add_program', data={
        'name': '',
        'description': 'A test remedial program',
        'test_id': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check that we were redirected to the counselor dashboard
    assert b'Counselor Dashboard' in response.data

    # Verify no program was added to database
    with app.app_context():
        final_count = Remedial.query.count()
        assert final_count == initial_count

def test_add_program_invalid_test_id(client):
    """Test adding a program with invalid test_id."""
    login_counselor(client)

    # Count programs before attempt
    with app.app_context():
        initial_count = Remedial.query.count()

    response = client.post('/counselor/add_program', data={
        'name': 'Test Program',
        'description': 'A test remedial program',
        'test_id': '999'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check that we were redirected to the counselor dashboard
    assert b'Counselor Dashboard' in response.data

    # Verify no program was added to database
    with app.app_context():
        final_count = Remedial.query.count()
        assert final_count == initial_count

def test_add_program_unauthorized(client):
    """Test adding a program without counselor privileges."""
    login_student(client)

    response = client.post('/counselor/add_program', data={
        'name': 'Test Program',
        'description': 'A test remedial program',
        'test_id': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Access denied. Counselor or Admin privileges required.' in response.data

def test_delete_program_success(client):
    """Test deleting a program successfully."""
    login_counselor(client)

    # First add a program
    client.post('/counselor/add_program', data={
        'name': 'Program to Delete',
        'description': 'This will be deleted',
        'test_id': '1'
    })

    # Get the program ID
    with app.app_context():
        program = Remedial.query.filter_by(name='Program to Delete').first()
        program_id = program.id

    # Delete the program
    response = client.post(f'/counselor/delete_program/{program_id}', follow_redirects=True)

    assert response.status_code == 200
    # Check that we were redirected to the counselor dashboard
    assert b'Counselor Dashboard' in response.data

    # Verify program was deleted
    with app.app_context():
        deleted_program = Remedial.query.get(program_id)
        assert deleted_program is None

def test_delete_program_not_found(client):
    """Test deleting a non-existent program."""
    login_counselor(client)

    response = client.post('/counselor/delete_program/999', follow_redirects=True)

    assert response.status_code == 200
    # Check that we were redirected to the counselor dashboard
    assert b'Counselor Dashboard' in response.data

def test_delete_program_unauthorized(client):
    """Test deleting a program without counselor privileges."""
    login_student(client)

    response = client.post('/counselor/delete_program/1', follow_redirects=True)

    assert response.status_code == 200
    assert b'Access denied. Counselor or Admin privileges required.' in response.data

def test_add_assessment_success(client):
    """Test adding an assessment successfully."""
    login_counselor(client)

    response = client.post('/counselor/add_assessment', data={
        'name': 'New Test Assessment',
        'description': 'A new test assessment',
        'difficulty_level': 'hard'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

    # Verify assessment was added to database
    with app.app_context():
        assessment = Test.query.filter_by(name='New Test Assessment').first()
        assert assessment is not None
        assert assessment.description == 'A new test assessment'
        assert assessment.difficulty_level == 'hard'

def test_add_assessment_missing_fields(client):
    """Test adding an assessment with missing fields."""
    login_counselor(client)

    # Count assessments before attempt
    with app.app_context():
        initial_count = Test.query.count()

    response = client.post('/counselor/add_assessment', data={
        'name': '',
        'description': 'A test assessment',
        'difficulty_level': 'medium'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

    # Verify no assessment was added
    with app.app_context():
        final_count = Test.query.count()
        assert final_count == initial_count

def test_add_assessment_invalid_difficulty(client):
    """Test adding an assessment with invalid difficulty level."""
    login_counselor(client)

    response = client.post('/counselor/add_assessment', data={
        'name': 'Test Assessment',
        'description': 'A test assessment',
        'difficulty_level': 'invalid'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

    with app.app_context():
        assessment = Test.query.filter_by(name='Test Assessment').first()
        assert assessment.difficulty_level == 'medium'

def test_add_assessment_unauthorized(client):
    """Test adding an assessment without counselor privileges."""
    login_student(client)

    response = client.post('/counselor/add_assessment', data={
        'name': 'Test Assessment',
        'description': 'A test assessment',
        'difficulty_level': 'medium'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Access denied. Counselor or Admin privileges required.' in response.data

def test_delete_assessment_success(client):
    """Test deleting an assessment successfully."""
    login_counselor(client)

    # First add an assessment
    client.post('/counselor/add_assessment', data={
        'name': 'Assessment to Delete',
        'description': 'This will be deleted',
        'difficulty_level': 'easy'
    })

    # Get the assessment ID
    with app.app_context():
        assessment = Test.query.filter_by(name='Assessment to Delete').first()
        assessment_id = assessment.id

    # Delete the assessment
    response = client.post(f'/counselor/delete_assessment/{assessment_id}', follow_redirects=True)

    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

    # Verify assessment was deleted
    with app.app_context():
        deleted_assessment = Test.query.get(assessment_id)
        assert deleted_assessment is None

def test_delete_assessment_with_programs(client):
    """Test deleting an assessment that has associated programs."""
    login_counselor(client)

    # First add an assessment
    client.post('/counselor/add_assessment', data={
        'name': 'Assessment with Programs',
        'description': 'Has associated programs',
        'difficulty_level': 'medium'
    })

    # Get the assessment ID and add a program to it
    with app.app_context():
        assessment = Test.query.filter_by(name='Assessment with Programs').first()
        assessment_id = assessment.id

        program = Remedial(
            test_id=assessment_id,
            name='Test Program',
            description='Test description'
        )
        db.session.add(program)
        db.session.commit()

    # Try to delete the assessment
    response = client.post(f'/counselor/delete_assessment/{assessment_id}', follow_redirects=True)

    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

    # Verify assessment was not deleted
    with app.app_context():
        assessment = Test.query.get(assessment_id)
        assert assessment is not None

def test_delete_assessment_not_found(client):
    """Test deleting a non-existent assessment."""
    login_counselor(client)

    response = client.post('/counselor/delete_assessment/999', follow_redirects=True)

    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

def test_delete_assessment_unauthorized(client):
    """Test deleting an assessment without counselor privileges."""
    login_student(client)

    response = client.post('/counselor/delete_assessment/1', follow_redirects=True)

    assert response.status_code == 200
    assert b'Access denied. Counselor or Admin privileges required.' in response.data

def test_counselor_login_redirects_to_dashboard(client):
    """Test that counselor login redirects to dashboard."""
    response = client.post('/login', data={
        'email': 'counselor@lddetector.com',
        'password': 'counselor123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Counselor Dashboard' in response.data

def test_counselor_dashboard_total_student_count(client):
    """Test that counselor dashboard displays correct total student count."""
    login_counselor(client)

    # Add a few students
    student1 = User(
        name='Student One',
        email='student1@test.com',
        role='student',
        age=20,
        gender='Male',
        course='CS',
        year='2023'
    )
    student1.set_password('password123')
    db.session.add(student1)

    student2 = User(
        name='Student Two',
        email='student2@test.com',
        role='student',
        age=21,
        gender='Female',
        course='Math',
        year='2023'
    )
    student2.set_password('password123')
    db.session.add(student2)
    db.session.commit()

    response = client.get('/counselor')
    assert response.status_code == 200
    assert b'Total Students:' in response.data
    assert b'<span id="total-students">3</span>' in response.data

def test_counselor_dashboard_student_details(client):
    """Test that counselor dashboard shows student details including gender and get-to-know-you."""
    login_counselor(client)

    # Add a student with get-to-know-you data
    student = User(
        name='Test Student',
        email='teststudent@test.com',
        role='student',
        age=22,
        gender='Non-binary',
        course='Engineering',
        year='2024',
        completed_get_to_know_you=True,
        g2k_learning_style='Visual',
        g2k_diagnosed_difficulties='Dyslexia',
        g2k_age_group='18-25'
    )
    student.set_password('password123')
    db.session.add(student)
    db.session.commit()

    response = client.get('/counselor')
    assert response.status_code == 200
    assert b'Test Student' in response.data
    assert b'Non-binary' in response.data
    assert b'Engineering' in response.data
    assert b'Visual' in response.data
    assert b'Dyslexia' in response.data
    assert b'18-25' in response.data

def test_counselor_required_decorator(client):
    """Test that counselor_required decorator works properly."""
    # Test without login
    response = client.get('/counselor', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page.' in response.data

    # Test with student login
    login_student(client)
    response = client.get('/counselor', follow_redirects=True)
    assert response.status_code == 200
    assert b'Access denied. Counselor or Admin privileges required.' in response.data

    # Test with counselor login
    login_counselor(client)
    response = client.get('/counselor', follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Counselor' in response.data  # Should show counselor dashboard
