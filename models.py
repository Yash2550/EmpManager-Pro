from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─── User Model ───────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin, hr, employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='user_account', uselist=False, foreign_keys=[employee_id])
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ─── Department Model ─────────────────────────────────────────
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    head_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    employees = db.relationship('Employee', backref='department', lazy='dynamic',
                                foreign_keys='Employee.department_id')
    head = db.relationship('Employee', foreign_keys=[head_id], uselist=False)

# ─── Employee Model ───────────────────────────────────────────
class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    designation = db.Column(db.String(100))
    date_of_joining = db.Column(db.Date, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    salary = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, inactive, terminated
    avatar = db.Column(db.String(256), default='default.png')
    qr_code = db.Column(db.String(256))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    blood_group = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic')
    leave_requests = db.relationship('LeaveRequest', backref='employee', lazy='dynamic')
    leave_balances = db.relationship('LeaveBalance', backref='employee', lazy='dynamic')
    payrolls = db.relationship('Payroll', backref='employee', lazy='dynamic')
    performances = db.relationship('Performance', backref='employee', lazy='dynamic',
                                   foreign_keys='Performance.employee_id')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# ─── Attendance Model ─────────────────────────────────────────
class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')  # present, absent, late, half-day, on-leave
    hours_worked = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_attendance_per_day'),
    )

# ─── Leave Request Model ──────────────────────────────────────
class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)  # casual, sick, earned, maternity, paternity
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    approver = db.relationship('User', foreign_keys=[approved_by])

# ─── Leave Balance Model ──────────────────────────────────────
class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)
    total = db.Column(db.Integer, default=0)
    used = db.Column(db.Integer, default=0)
    remaining = db.Column(db.Integer, default=0)
    year = db.Column(db.Integer, default=2026)

# ─── Payroll Model ────────────────────────────────────────────
class Payroll(db.Model):
    __tablename__ = 'payrolls'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    basic_salary = db.Column(db.Float, default=0.0)
    hra = db.Column(db.Float, default=0.0)  # House Rent Allowance
    da = db.Column(db.Float, default=0.0)   # Dearness Allowance
    ta = db.Column(db.Float, default=0.0)   # Travel Allowance
    bonus = db.Column(db.Float, default=0.0)
    pf_deduction = db.Column(db.Float, default=0.0)     # Provident Fund
    tax_deduction = db.Column(db.Float, default=0.0)     # Income Tax
    other_deductions = db.Column(db.Float, default=0.0)
    gross_salary = db.Column(db.Float, default=0.0)
    net_salary = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='generated')  # generated, paid
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year', name='unique_payroll_per_month'),
    )

# ─── Performance Review Model ─────────────────────────────────
class Performance(db.Model):
    __tablename__ = 'performances'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    period = db.Column(db.String(20), nullable=False)  # Q1-2026, Q2-2026, etc.
    rating = db.Column(db.Float, default=0.0)  # 1-5 scale
    goals_met = db.Column(db.Integer, default=0)
    goals_total = db.Column(db.Integer, default=0)
    strengths = db.Column(db.Text)
    improvements = db.Column(db.Text)
    comments = db.Column(db.Text)
    review_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reviewer = db.relationship('Employee', foreign_keys=[reviewer_id])

# ─── Notification Model ───────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
