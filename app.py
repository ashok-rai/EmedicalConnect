import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Set secret key
    app.secret_key = os.environ.get("SESSION_SECRET")
    
    # Apply proxy fix for proper URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    with app.app_context():
        # Import models for database creation
        from models import User, Patient, Doctor, Admin, Appointment, HealthRecord, Message, Feedback
        
        # Create database tables if they don't exist
        db.create_all()
        
        # Import and register blueprints
        from routes import main_bp, auth_bp, patient_bp, doctor_bp, admin_bp, appointment_bp, health_record_bp, chat_bp, feedback_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(patient_bp, url_prefix='/patient')
        app.register_blueprint(doctor_bp, url_prefix='/doctor')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(appointment_bp, url_prefix='/appointments')
        app.register_blueprint(health_record_bp, url_prefix='/records')
        app.register_blueprint(chat_bp, url_prefix='/chat')
        app.register_blueprint(feedback_bp, url_prefix='/feedback')
        
        return app
