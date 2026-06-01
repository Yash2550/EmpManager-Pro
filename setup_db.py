"""
Safe Database Setup Script
Creates tables if they don't exist and seeds the admin user.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Department, Employee
from datetime import date

def setup(app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        print("Checking database connection...")
        try:
            # Create tables (won't error if they already exist, usually)
            db.create_all()
            print("[OK] Tables created or already exist.")

            # 1. Seed Admin
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Seeding admin user...");
                admin = User(username='admin', email='admin@company.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                print("[OK] Admin created.")
            else:
                admin.set_password('admin123')
                print("[OK] Admin password reset.")

            # 2. Seed a Department and Employee for HR/Employee roles
            dept = Department.query.filter_by(name='Engineering').first()
            if not dept:
                dept = Department(name='Engineering', description='Tech Team')
                db.session.add(dept)
                db.session.flush()

            from models import Employee
            hr_emp = Employee.query.filter_by(emp_code='EMP-0001').first()
            if not hr_emp:
                hr_emp = Employee(
                    emp_code='EMP-0001', first_name='HR', last_name='Manager',
                    email='hr@company.com', department_id=dept.id, 
                    designation='HR Manager', date_of_joining=date(2024, 1, 1),
                    status='active'
                )
                db.session.add(hr_emp)
                db.session.flush()

            std_emp = Employee.query.filter_by(emp_code='EMP-0002').first()
            if not std_emp:
                std_emp = Employee(
                    emp_code='EMP-0002', first_name='Aarav', last_name='Sharma',
                    email='aarav.sharma@company.com', department_id=dept.id, 
                    designation='Senior Developer', date_of_joining=date(2024, 1, 1),
                    status='active'
                )
                db.session.add(std_emp)
                db.session.flush()

            # 3. Seed HR User
            hr_user = User.query.filter_by(username='hrmanager').first()
            if not hr_user:
                hr_user = User(username='hrmanager', email='hr@company.com', role='hr', employee_id=hr_emp.id)
                hr_user.set_password('hr123')
                db.session.add(hr_user)
                print("[OK] HR Manager created (hrmanager / hr123)")

            # 4. Seed Employee User
            emp_user = User.query.filter_by(username='aarav.sharma').first()
            if not emp_user:
                emp_user = User(username='aarav.sharma', email='aarav.sharma@company.com', role='employee', employee_id=std_emp.id)
                emp_user.set_password('pass123')
                db.session.add(emp_user)
                print("[OK] Employee created (aarav.sharma / pass123)")

            db.session.commit()
            print("\nAll test accounts are ready!")

            print("\nDatabase is ready!")

        except Exception as e:
            print(f"[ERROR] Database setup failed: {e}")

if __name__ == '__main__':
    setup()
