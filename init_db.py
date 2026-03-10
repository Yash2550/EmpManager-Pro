"""
Database Initialization & Seed Script
Run this once to create all tables and populate with sample data.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Department, Employee, Attendance, LeaveRequest, LeaveBalance, Payroll, Performance, Notification
from datetime import datetime, date, timedelta
from utils.qr_generator import generate_qr_code
import random

app = create_app()

def seed_data():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("[OK] Tables created.")

        # ── Departments ──────────────────────────────
        departments = [
            Department(name='Engineering', description='Software development and engineering team'),
            Department(name='Human Resources', description='People management and recruitment'),
            Department(name='Finance', description='Financial planning, accounting and budgeting'),
            Department(name='Marketing', description='Brand management and digital marketing'),
            Department(name='Sales', description='Client acquisition and revenue generation'),
            Department(name='Operations', description='Day-to-day business operations'),
            Department(name='Design', description='UI/UX and graphic design team'),
            Department(name='Support', description='Customer support and service desk'),
        ]
        db.session.add_all(departments)
        db.session.flush()
        print(f"[OK] {len(departments)} departments created.")

        # ── Employees ────────────────────────────────
        emp_data = [
            ('Aarav', 'Sharma', 'aarav.sharma@company.com', '9876543210', 1, 'Senior Developer', 85000, 'M', 'A+'),
            ('Priya', 'Patel', 'priya.patel@company.com', '9876543211', 1, 'Full Stack Developer', 72000, 'F', 'B+'),
            ('Rahul', 'Kumar', 'rahul.kumar@company.com', '9876543212', 2, 'HR Manager', 78000, 'M', 'O+'),
            ('Sneha', 'Reddy', 'sneha.reddy@company.com', '9876543213', 3, 'Financial Analyst', 68000, 'F', 'AB+'),
            ('Vikram', 'Singh', 'vikram.singh@company.com', '9876543214', 4, 'Marketing Lead', 75000, 'M', 'A-'),
            ('Anita', 'Desai', 'anita.desai@company.com', '9876543215', 5, 'Sales Executive', 62000, 'F', 'B-'),
            ('Karthik', 'Nair', 'karthik.nair@company.com', '9876543216', 6, 'Operations Manager', 80000, 'M', 'O-'),
            ('Deepa', 'Menon', 'deepa.menon@company.com', '9876543217', 7, 'UI/UX Designer', 70000, 'F', 'A+'),
            ('Arjun', 'Gupta', 'arjun.gupta@company.com', '9876543218', 1, 'Backend Developer', 76000, 'M', 'B+'),
            ('Meera', 'Iyer', 'meera.iyer@company.com', '9876543219', 8, 'Support Lead', 65000, 'F', 'O+'),
            ('Rohan', 'Joshi', 'rohan.joshi@company.com', '9876543220', 1, 'DevOps Engineer', 82000, 'M', 'AB-'),
            ('Kavya', 'Rao', 'kavya.rao@company.com', '9876543221', 2, 'HR Executive', 55000, 'F', 'A+'),
            ('Aditya', 'Verma', 'aditya.verma@company.com', '9876543222', 3, 'Accountant', 58000, 'M', 'B+'),
            ('Divya', 'Kapoor', 'divya.kapoor@company.com', '9876543223', 4, 'Content Writer', 52000, 'F', 'O+'),
            ('Nikhil', 'Mehta', 'nikhil.mehta@company.com', '9876543224', 5, 'Sales Manager', 78000, 'M', 'A-'),
            ('Pooja', 'Shah', 'pooja.shah@company.com', '9876543225', 6, 'Logistics Coordinator', 56000, 'F', 'B-'),
            ('Suresh', 'Pillai', 'suresh.pillai@company.com', '9876543226', 7, 'Graphic Designer', 60000, 'M', 'O+'),
            ('Ritu', 'Agarwal', 'ritu.agarwal@company.com', '9876543227', 8, 'Support Executive', 48000, 'F', 'AB+'),
            ('Manish', 'Tiwari', 'manish.tiwari@company.com', '9876543228', 1, 'QA Engineer', 68000, 'M', 'A+'),
            ('Swati', 'Mishra', 'swati.mishra@company.com', '9876543229', 2, 'Recruiter', 52000, 'F', 'B+'),
        ]

        qr_dir = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)

        employees = []
        for i, (fn, ln, email, phone, dept_id, desig, salary, gender, bg) in enumerate(emp_data, 1):
            doj = date(2024, 1, 1) + timedelta(days=random.randint(0, 500))
            dob = date(1990, 1, 1) + timedelta(days=random.randint(0, 3650))
            emp_code = f"EMP-{i:04d}"
            
            emp = Employee(
                emp_code=emp_code, first_name=fn, last_name=ln,
                email=email, phone=phone, department_id=dept_id,
                designation=desig, date_of_joining=doj, date_of_birth=dob,
                gender=gender, salary=salary, blood_group=bg,
                address=f'{random.randint(1,500)}, Sector {random.randint(1,50)}, City',
                emergency_contact=f'{fn} Family', emergency_phone=f'98765{random.randint(10000,99999)}',
                status='active'
            )
            employees.append(emp)
        
        db.session.add_all(employees)
        db.session.flush()

        # Generate QR codes
        for emp in employees:
            qr_data = f"EMPMGMT|{emp.emp_code}|{emp.id}|{emp.full_name}"
            qr_filename = f"qr_{emp.emp_code}.png"
            try:
                generate_qr_code(qr_data, qr_filename, qr_dir)
                emp.qr_code = qr_filename
            except Exception:
                emp.qr_code = None

        print(f"[OK] {len(employees)} employees created with QR codes.")

        # ── Users (Admin, HR, Employee accounts) ─────
        admin_user = User(username='admin', email='admin@company.com', role='admin')
        admin_user.set_password('admin123')
        
        hr_user = User(username='hrmanager', email='hr@company.com', role='hr', employee_id=3)
        hr_user.set_password('hr123')
        
        users = [admin_user, hr_user]
        for emp in employees:
            uname = emp.first_name.lower() + '.' + emp.last_name.lower()
            u = User(username=uname, email=emp.email, role='employee', employee_id=emp.id)
            u.set_password('pass123')
            users.append(u)
        
        db.session.add_all(users)
        db.session.flush()
        print(f"[OK] {len(users)} user accounts created.")

        # ── Attendance (last 30 days) ────────────────
        att_count = 0
        today = date.today()
        for emp in employees:
            for d in range(30):
                att_date = today - timedelta(days=d)
                if att_date.weekday() >= 5:  # skip weekends
                    continue
                is_present = random.random() > 0.1  # 90% attendance rate
                if is_present:
                    hour_in = random.randint(8, 10)
                    min_in = random.randint(0, 59)
                    check_in = datetime(att_date.year, att_date.month, att_date.day, hour_in, min_in)
                    hour_out = random.randint(17, 19)
                    min_out = random.randint(0, 59)
                    check_out = datetime(att_date.year, att_date.month, att_date.day, hour_out, min_out)
                    hours = (check_out - check_in).total_seconds() / 3600
                    status = 'late' if hour_in >= 10 else 'present'
                else:
                    check_in = None
                    check_out = None
                    hours = 0
                    status = 'absent'
                
                att = Attendance(
                    employee_id=emp.id, date=att_date,
                    check_in=check_in, check_out=check_out,
                    hours_worked=round(hours, 1), status=status
                )
                db.session.add(att)
                att_count += 1
        print(f"[OK] {att_count} attendance records created.")

        # ── Leave Balances ───────────────────────────
        leave_types = {
            'casual': 12, 'sick': 10, 'earned': 15,
            'maternity': 180, 'paternity': 15
        }
        lb_count = 0
        for emp in employees:
            for lt, total in leave_types.items():
                if lt == 'maternity' and emp.gender == 'M':
                    continue
                if lt == 'paternity' and emp.gender == 'F':
                    continue
                used = random.randint(0, min(4, total))
                lb = LeaveBalance(
                    employee_id=emp.id, leave_type=lt,
                    total=total, used=used, remaining=total - used, year=2026
                )
                db.session.add(lb)
                lb_count += 1
        print(f"[OK] {lb_count} leave balances created.")

        # ── Leave Requests (some sample) ─────────────
        statuses = ['pending', 'approved', 'rejected']
        lr_count = 0
        for emp in employees[:10]:
            for _ in range(random.randint(0, 3)):
                start = today + timedelta(days=random.randint(1, 60))
                days = random.randint(1, 5)
                end = start + timedelta(days=days - 1)
                lr = LeaveRequest(
                    employee_id=emp.id,
                    leave_type=random.choice(['casual', 'sick', 'earned']),
                    start_date=start, end_date=end, days=days,
                    reason='Personal / Medical reasons',
                    status=random.choice(statuses)
                )
                db.session.add(lr)
                lr_count += 1
        print(f"[OK] {lr_count} leave requests created.")

        # ── Payroll (last 2 months) ──────────────────
        pr_count = 0
        for emp in employees:
            for month_offset in range(2):
                m = today.month - month_offset
                y = today.year
                if m <= 0:
                    m += 12
                    y -= 1
                basic = emp.salary
                hra = round(basic * 0.40, 2)
                da = round(basic * 0.10, 2)
                ta = round(basic * 0.05, 2)
                bonus = 0
                gross = basic + hra + da + ta + bonus
                pf = round(basic * 0.12, 2)
                tax = round(gross * 0.10, 2) if gross > 50000 else 0
                other = round(random.uniform(0, 500), 2)
                net = round(gross - pf - tax - other, 2)
                
                p = Payroll(
                    employee_id=emp.id, month=m, year=y,
                    basic_salary=basic, hra=hra, da=da, ta=ta,
                    bonus=bonus, pf_deduction=pf, tax_deduction=tax,
                    other_deductions=other, gross_salary=gross,
                    net_salary=net, status='paid' if month_offset > 0 else 'generated'
                )
                db.session.add(p)
                pr_count += 1
        print(f"[OK] {pr_count} payroll records created.")

        # ── Performance Reviews ──────────────────────
        perf_count = 0
        for emp in employees:
            perf = Performance(
                employee_id=emp.id,
                reviewer_id=employees[0].id if emp.id != employees[0].id else employees[1].id,
                period='Q4-2025',
                rating=round(random.uniform(2.5, 5.0), 1),
                goals_met=random.randint(3, 8),
                goals_total=8,
                strengths='Strong technical skills, good team player',
                improvements='Time management, documentation',
                comments='Consistent performer with growth potential',
                review_date=date(2025, 12, 15)
            )
            db.session.add(perf)
            perf_count += 1
        print(f"[OK] {perf_count} performance reviews created.")

        # ── Notifications ────────────────────────────
        notif_msgs = [
            ('Welcome', 'Welcome to the Employee Management System!', 'info'),
            ('Payroll Generated', 'Your payslip for this month has been generated.', 'success'),
            ('Leave Approved', 'Your casual leave request has been approved.', 'success'),
            ('Review Due', 'Your quarterly performance review is due.', 'warning'),
        ]
        for u in users[:5]:
            for title, msg, ntype in notif_msgs:
                n = Notification(user_id=u.id, title=title, message=msg, type=ntype)
                db.session.add(n)

        db.session.commit()
        print("\nDatabase seeded successfully!")
        print("=" * 50)
        print("  Admin Login: admin / admin123")
        print("  HR Login:    hrmanager / hr123")
        print("  Employee:    aarav.sharma / pass123")
        print("=" * 50)


if __name__ == '__main__':
    seed_data()
