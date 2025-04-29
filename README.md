# EmedicalConnect

EmedicalConnect is a web-based platform for managing digital health records, doctor appointments, prescriptions, and secure messaging between patients and healthcare providers.

## Features

- User authentication and account management
- Doctor and patient profiles
- Appointment scheduling and management
- Digital health record uploads (PDF, images, documents)
- Prescription management
- Secure messaging between users
- Admin interface for managing users and records

## Tech Stack

- Python 3.11+
- Django 5.x
- PostgreSQL (or SQLite for development)
- Bootstrap 5 (frontend)
- JavaScript (custom scripts)
- [See `pyproject.toml`](pyproject.toml) for all dependencies

## Project Structure

- `accounts/` – User authentication, profiles, and related views
- `appointments/` – Appointment models, forms, and views
- `medical_records/` – Health record and prescription management
- `messaging/` – Secure user messaging
- `emedic/` – Django project settings and URLs
- `static/` – Static files (CSS, JS, images)
- `templates/` – HTML templates
- `manage.py` – Django management script

## Setup Instructions

1. **Clone the repository**
    ```sh
    git clone <repo-url>
    cd EmedicalConnect
    ```

2. **Create and activate a virtual environment**
    ```sh
    python3 -m venv env
    source env/bin/activate
    ```

3. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

4. **Apply migrations**
    ```sh
    python manage.py migrate
    ```

5. **Create a superuser (admin)**
    ```sh
    python manage.py createsuperuser
    ```

6. **Run the development server**
    ```sh
    python manage.py runserver
    ```

7. **Access the app**
    - Visit [http://localhost:8000/](http://localhost:8000/) in your browser.

## Testing

To run tests:
```sh
python manage.py test
```

## File Uploads

- Supported formats: PDF, JPG, PNG, DOC, DOCX
- Max file size: 10–16MB (see form help texts)
- Files are stored in the `media/` directory (see `.gitignore`)

## Environment Variables

- Copy `.env.example` to `.env` and set your environment variables as needed.

## License

This project is for educational/demo purposes. See `LICENSE` for details.

---

For more details, see the code in [accounts/](accounts/), [appointments/](appointments/), [medical_records/](medical_records/), and [emedic/](emedic/).