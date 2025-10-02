# Learning Disability Detector

This is a Flask-based web application designed to help detect learning disabilities such as dyslexia and memory-related issues through a series of assessments.

## Features

- User registration and login with role-based access (student, counselor, admin)
- "Get to Know You" survey for new students to capture learning style and background
- Assessments for dyslexia, dyscalculia, and memory
- Dashboard for students to view their profile and assessment results
- Admin and counselor dashboards to manage users and view results
- Password reset via email
- Export assessment results to CSV

## Installation

1. Clone the repository:

```bash
git clone https://github.com/J4skii/Learning-Disability-Detector.git
cd Learning-Disability-Detector
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set environment variables (optional but recommended for production):

- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - Database connection string (default is SQLite)
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER` - For email functionality

5. Run the application:

```bash
python app.py
```

6. Access the app at `http://127.0.0.1:5000`

## Usage

- Sign up as a new student
- Complete the "Get to Know You" survey
- Take assessments and view results on your dashboard
- Admins and counselors can manage users and view reports

## Recent Updates

- Enhanced counselor dashboard: Added total student count display, gender column, get-to-know-you column to students table, implemented add/delete modals for programs and assessments with confirmation prompts, and JavaScript for confirmation dialogs.
- Added new assessment templates: assessments.html, test_flash_cards.html, updated test_dyslexia.html, test_dyscalculia.html, and test_memory.html.
- Added database migrations: Alembic setup with initial migration for dyslexia tests and remedial schema.
- Updated app.py: Added routes for adding/deleting programs and assessments, ensured counselor_required decorator on new routes.
- Added test_app.py for application testing.
- Updated requirements.txt with new dependencies.
- Updated models.py with new schema changes.
- Updated TODO.md with completed tasks.

## Notes

- Routing for the pages needs to be double checked.
- Programs content is required.
- Memory and phonetics content for the assessment is required.

## License

MIT License

## Contact

For questions or support, please open an issue on GitHub.
