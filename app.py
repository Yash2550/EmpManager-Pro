import os
from flask import Flask, redirect, url_for, render_template, render_template_string
from flask_login import LoginManager
from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure directories exist
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/img/avatars'), exist_ok=True)
    os.makedirs(app.config.get('QR_FOLDER', 'static/qrcodes'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'img'), exist_ok=True)
    
    # Init extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(employee_bp)
    
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
