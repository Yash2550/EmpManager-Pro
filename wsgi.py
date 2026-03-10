"""
WSGI entry point for production deployment.
Creates the Flask app via the factory function in app.py.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run()
