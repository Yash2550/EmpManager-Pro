import os
import sys
print(f"DEBUG: Current Directory: {os.getcwd()}")
print(f"DEBUG: Directory Contents: {os.listdir(os.getcwd())}")

from flask import Flask, app, redirect, url_for, render_template, render_template_string
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Masked DB URL logging for debugging
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url and '@' in db_url:
        try:
            prefix, suffix = db_url.split('@', 1)
            # Masking password in protocol://user:pass@host format
            protocol_part = prefix.split('//', 1)[0] + '//' 
            user_part = prefix.split('//', 1)[1].split(':', 1)[0]
            print(f"DEBUG: Database connection target: {suffix.split('/', 1)[0]} (using {protocol_part}{user_part}:****)")
        except Exception:
            print("DEBUG: DATABASE_URL is set but format is non-standard for masking.")
    
    # Ensure directories exist
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/img/avatars'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'img'), exist_ok=True)
    os.makedirs(app.config.get('ML_MODELS_DIR', 'ml_models'), exist_ok=True)


    
    # Diagnostic database connection check and fallback
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url and db_url.startswith('postgresql'):
        from sqlalchemy import create_engine
        print("DEBUG: Testing remote database connection...")
        try:
            # Create engine with a short timeout to avoid hanging
            engine = create_engine(db_url, connect_args={'connect_timeout': 3})
            with engine.connect() as conn:
                pass
            engine.dispose()
            print("DEBUG: Remote database connection successful.")
        except Exception as e:
            print("\n" + "="*80)
            print("CRITICAL DATABASE CONNECTION ERROR")
            print("="*80)
            print(f"Failed to connect to remote database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
            print(f"Error details: {e}")
            print("-"*80)
            
            # Fall back to SQLite in development/debug mode or on Hugging Face Spaces
            is_huggingface = 'SPACE_ID' in os.environ or 'SPACE_TITLE' in os.environ
            if app.debug or os.environ.get('FLASK_ENV') == 'development' or is_huggingface:
                sqlite_url = 'sqlite:///' + os.path.join(app.root_path, 'employee.db')
                print(f"DEVELOPMENT FALLBACK: Switching to local SQLite database:")
                print(f"  {sqlite_url}")
                print("Your local database is fully seeded and ready to use!")
                print("="*80 + "\n")
                app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_url
                # Clear PostgreSQL-specific engine options to avoid SQLite driver TypeError
                app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                    'pool_pre_ping': True,
                    'pool_recycle': 300,
                    'connect_args': {}
                }
            else:
                print("Please check your remote database server and credentials.")
                print("="*80 + "\n")

    # Init extensions
    from models import db
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Automatically initialize and seed the database if the tables do not exist
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if not inspector.has_table("users"):
                print("\n" + "="*80)
                print("DATABASE INITIALIZATION REQUIRED: 'users' table not found.")
                print("="*80)
                
                db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
                if 'sqlite' in db_url:
                    print("Detected SQLite database. Performing full database seeding with demo data...")
                    from init_db import seed_data
                    seed_data(app)
                else:
                    print("Detected remote PostgreSQL database. Performing safe database setup...")
                    from setup_db import setup as safe_setup
                    safe_setup(app)
                print("="*80 + "\n")
        except Exception as e:
            print(f"WARNING: Automatic database initialization failed: {e}")
    
    login_manager = LoginManager()
    login_manager.init_app(app) 
    login_manager.login_view = 'auth.login' # type: ignore
    login_manager.login_message_category = 'warning'
    
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id): 
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.hr import hr_bp
    from routes.attendance import attendance_bp

    from routes.employee import employee_bp
    from routes.chatbot import chatbot_bp
    from routes.ml import ml_bp
    from routes.voice import voice_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(attendance_bp)

    app.register_blueprint(employee_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(voice_bp)
    
    # Template context helpers
    from utils.helpers import format_currency, format_date, format_datetime, time_since
        
    @app.context_processor
    def utility_processor():
        return dict(    
            format_currency=format_currency,
            format_date=format_date,
            format_datetime=format_datetime,
            time_since=time_since
        )
    
    # Company landing page
    @app.route('/')
    def index():
        return render_template('landing.html')
    
    # Error handlers 
    @app.errorhandler(403)
    def forbidden(e):
        return render_template_string('''
        <!DOCTYPE html><html><head><title>403 - Access Denied</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        </head><body class="auth-page"><div style="text-align:center">
        <h1 style="font-size:4rem;color:#dc2626;margin-bottom:1rem"><i class="fas fa-lock"></i></h1>
        <h2>403 - Access Denied</h2>
        <p style="color:#64748b;margin:1rem 0">You do not have permission to access this page.</p>
        <a href="/" class="btn btn-primary"><i class="fas fa-home"></i> Go Home</a>
        </div></body></html>'''), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template_string('''
        <!DOCTYPE html><html><head><title>404 - Not Found</title>
        <link rel="stylesheet" href="/static/css/style.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        </head><body class="auth-page"><div style="text-align:center">
        <h1 style="font-size:4rem;color:#2563eb;margin-bottom:1rem"><i class="fas fa-compass"></i></h1>
        <h2>404 - Page Not Found</h2>
        <p style="color:#64748b;margin:1rem 0">The page you are looking for does not exist.</p>
        <a href="/" class="btn btn-primary"><i class="fas fa-home"></i> Go Home</a>
        </div></body></html>'''), 404
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
