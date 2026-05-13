"""
Safe Database Setup Script
Creates tables if they don't exist and seeds the admin user.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Department

app = create_app()

def setup():
    with app.app_context():
        print("Checking database connection...")
        try:
            # Create tables (won't error if they already exist, usually)
            db.create_all()
            print("[OK] Tables created or already exist.")

            # Seed Admin if not present
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Seeding admin user...")
                admin = User(username='admin', email='admin@company.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                print("[OK] Admin user created (admin / admin123)")
            else:
                print("[INFO] Admin user already exists. Resetting password to 'admin123'...")
                admin.set_password('admin123')
                db.session.commit()
                print("[OK] Admin password reset to 'admin123'")

            print("\nDatabase is ready!")

        except Exception as e:
            print(f"[ERROR] Database setup failed: {e}")

if __name__ == '__main__':
    setup()
