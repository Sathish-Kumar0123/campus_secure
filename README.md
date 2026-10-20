# CampusSecure — Django + MySQL academic portal

A learning project demonstrating authentication, role-based authorization, database relationships, frontend templates, CSRF protection, XSS-safe output, event roster verification, .

## Important security design
- Passwords are **not encrypted**. Django stores salted password hashes (PBKDF2 by default; Argon2 can be configured). Password hashes cannot be decrypted.
- Recoverable secrets would use encryption, but do not encrypt passwords.
- Django sessions are used for browser login. Login rotates the session key; logout is POST-only.
- Forms include CSRF tokens. Django templates autoescape variable output. Do not use `safe` on user-provided content.
- Roles are checked server-side. Students only query their own marks/attendance.
- A student report grants event attendance only if their own stored roll number is on the staff-maintained event roster. The student cannot enter a different roll number to pass verification.
- Browser pages use Django session authentication, and JWT access/refresh tokens are available for API clients through Simple JWT. This lets the project demonstrate both patterns. Session-authenticated unsafe requests remain CSRF-protected. JWT clients should send `Authorization: Bearer <access_token>` and must not put tokens in URLs.

## 1. Install prerequisites
Install Python 3.11+ and MySQL Server. On Windows, install the MySQL Connector/build prerequisites needed by `mysqlclient`. If `mysqlclient` fails to install, install the Microsoft C++ Build Tools and MySQL development libraries, or use a compatible Python/MySQL setup.

## 2. Create database
In MySQL Workbench or the MySQL CLI:
```sql
CREATE DATABASE college_portal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Create/use a MySQL user with permission to access this database. Avoid using a production root account.

## 3. Setup in VS Code terminal (PowerShell)
Open the `Dundi_django` folder, then run:
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and set your MySQL password and a unique `SECRET_KEY`. Keep `.env` private; it is ignored by Git.

## 4. Create tables and HOD
```powershell
python manage.py makemigrations portal
python manage.py migrate
python manage.py createsuperuser
```
For the superuser account, open Django admin at `/admin/`, edit that user's `Role` to `HOD`. The superuser's `is_staff`/`is_superuser` flags are separate from the app role.

Then start:
```powershell
python manage.py runserver
```
Open http://127.0.0.1:8000/

## 5. First-run workflow
1. Log in as the HOD (role set to HOD in admin).
2. HOD adds teacher accounts from the dashboard.
3. Teachers can add students, enter marks, record class attendance, create events, and maintain event rosters.
4. Students can register themselves (this starter allows self-registration as a student) or be created by a teacher/HOD.
5. Staff adds each attendee's roll number to the event roster based on the real attendance sheet.
6. Student submits a report. Attendance is credited only when the student's stored roll number is on that event's roster.

## JWT API token endpoints
- `POST /api/token/` with JSON `{"username":"...","password":"..."}` returns access and refresh tokens.
- `POST /api/token/refresh/` with JSON `{"refresh":"..."}` returns a new access token.
- These token endpoints authenticate users; they are a starting point for future DRF APIs. Any new API view must still enforce role/object-level permissions and should not expose data merely because a token is valid.

## Before production
This is an educational starter, not a production-audited system. Add tests, teacher-to-subject assignments, HOD approval workflows, audit logs, rate limiting, password reset, secure file upload validation/storage, backup/restore, and a review of privacy requirements. Keep `DEBUG=False`, set `ALLOWED_HOSTS`, use HTTPS, set a real secret key, and configure secure cookies. If using an SPA/mobile API, implement JWT deliberately rather than placing bearer tokens in localStorage by default.

## Useful security tests to perform
- Student cannot access add-student/add-teacher pages.
- Student marks/attendance show only their own rows.
- A student not on an event roster cannot receive event attendance.
- GET `/logout/` is not allowed; logout requires POST and CSRF.
- Invalid login does not reveal whether username or password was wrong.
- User-entered text renders as text, not executable HTML.
