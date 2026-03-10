from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Employee, Department, User, Attendance, LeaveRequest, Payroll
from utils.decorators import admin_required
from utils.qr_generator import generate_qr_code
from utils.export import export_employees_excel
from datetime import datetime, date, timedelta
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_employees = Employee.query.filter_by(status='active').count()
    total_departments = Department.query.count()
    
    today = date.today()
    present_today = Attendance.query.filter_by(date=today, status='present').count()
    late_today = Attendance.query.filter_by(date=today, status='late').count()
    absent_today = total_employees - present_today - late_today
    
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    
    recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(5).all()
    recent_leaves = LeaveRequest.query.order_by(LeaveRequest.created_at.desc()).limit(5).all()
    
    # Department distribution for chart
    departments = Department.query.all()
    dept_names = [d.name for d in departments]
    dept_counts = [d.employees.filter_by(status='active').count() for d in departments]
    
    # Attendance trend (last 7 days)
    att_dates = []
    att_present = []
    att_absent = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        if d.weekday() < 5:
            att_dates.append(d.strftime('%d %b'))
            p = Attendance.query.filter_by(date=d).filter(Attendance.status.in_(['present', 'late'])).count()
            att_present.append(p)
            att_absent.append(total_employees - p)
    
    # Monthly payroll total
    current_month_payroll = db.session.query(
        db.func.sum(Payroll.net_salary)
    ).filter_by(month=today.month, year=today.year).scalar() or 0
    
    return render_template('admin/dashboard.html',
        total_employees=total_employees,
        total_departments=total_departments,
        present_today=present_today + late_today,
        absent_today=absent_today,
        pending_leaves=pending_leaves,
        recent_employees=recent_employees,
        recent_leaves=recent_leaves,
        dept_names=dept_names,
        dept_counts=dept_counts,
        att_dates=att_dates,
        att_present=att_present,
        att_absent=att_absent,
        current_month_payroll=current_month_payroll
    )


@admin_bp.route('/employees')
@login_required
@admin_required
def employees():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    dept_filter = request.args.get('department', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = Employee.query
    
    if search:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f'%{search}%'),
                Employee.last_name.ilike(f'%{search}%'),
                Employee.emp_code.ilike(f'%{search}%'),
                Employee.email.ilike(f'%{search}%')
            )
        )
    if dept_filter:
        query = query.filter_by(department_id=int(dept_filter))
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    employees = query.order_by(Employee.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    departments = Department.query.all()
    
    return render_template('admin/employees.html',
        employees=employees, departments=departments,
        search=search, dept_filter=dept_filter, status_filter=status_filter
    )


@admin_bp.route('/employees/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employee():
    if request.method == 'POST':
        emp_count = Employee.query.count() + 1
        emp_code = f"EMP-{emp_count:04d}"
        
        emp = Employee(
            emp_code=emp_code,
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            phone=request.form.get('phone', ''),
            department_id=int(request.form['department_id']),
            designation=request.form.get('designation', ''),
            date_of_joining=datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d').date(),
            date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
            gender=request.form.get('gender', ''),
            salary=float(request.form.get('salary', 0)),
            address=request.form.get('address', ''),
            blood_group=request.form.get('blood_group', ''),
            emergency_contact=request.form.get('emergency_contact', ''),
            emergency_phone=request.form.get('emergency_phone', ''),
            status='active'
        )
        db.session.add(emp)
        db.session.flush()
        
        # Generate QR code
        qr_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'qrcodes')
        if not os.path.exists(qr_dir):
            qr_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'qrcodes')
        from flask import current_app
        qr_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)
        qr_data = f"EMPMGMT|{emp.emp_code}|{emp.id}|{emp.full_name}"
        qr_filename = f"qr_{emp.emp_code}.png"
        generate_qr_code(qr_data, qr_filename, qr_dir)
        emp.qr_code = qr_filename
        
        # Create user account
        username = f"{emp.first_name.lower()}.{emp.last_name.lower()}"
        user = User(username=username, email=emp.email, role='employee', employee_id=emp.id)
        user.set_password('pass123')
        db.session.add(user)
        
        # Create leave balances
        from models import LeaveBalance
        leave_types = {'casual': 12, 'sick': 10, 'earned': 15}
        if emp.gender == 'F':
            leave_types['maternity'] = 180
        else:
            leave_types['paternity'] = 15
        for lt, total in leave_types.items():
            lb = LeaveBalance(employee_id=emp.id, leave_type=lt, total=total, used=0, remaining=total, year=2026)
            db.session.add(lb)
        
        db.session.commit()
        flash(f'Employee {emp.full_name} added successfully!', 'success')
        return redirect(url_for('admin.employees'))
    
    departments = Department.query.all()
    return render_template('admin/employee_form.html', employee=None, departments=departments, action='Add')


@admin_bp.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_employee(id):
    emp = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        emp.first_name = request.form['first_name']
        emp.last_name = request.form['last_name']
        emp.email = request.form['email']
        emp.phone = request.form.get('phone', '')
        emp.department_id = int(request.form['department_id'])
        emp.designation = request.form.get('designation', '')
        emp.date_of_joining = datetime.strptime(request.form['date_of_joining'], '%Y-%m-%d').date()
        if request.form.get('date_of_birth'):
            emp.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
        emp.gender = request.form.get('gender', '')
        emp.salary = float(request.form.get('salary', 0))
        emp.address = request.form.get('address', '')
        emp.blood_group = request.form.get('blood_group', '')
        emp.emergency_contact = request.form.get('emergency_contact', '')
        emp.emergency_phone = request.form.get('emergency_phone', '')
        emp.status = request.form.get('status', 'active')
        
        db.session.commit()
        flash(f'Employee {emp.full_name} updated successfully!', 'success')
        return redirect(url_for('admin.employee_detail', id=emp.id))
    
    departments = Department.query.all()
    return render_template('admin/employee_form.html', employee=emp, departments=departments, action='Edit')


@admin_bp.route('/employees/<int:id>')
@login_required
@admin_required
def employee_detail(id):
    emp = Employee.query.get_or_404(id)
    recent_attendance = Attendance.query.filter_by(employee_id=id).order_by(Attendance.date.desc()).limit(10).all()
    recent_leaves = LeaveRequest.query.filter_by(employee_id=id).order_by(LeaveRequest.created_at.desc()).limit(5).all()
    latest_payroll = Payroll.query.filter_by(employee_id=id).order_by(Payroll.year.desc(), Payroll.month.desc()).first()
    from models import LeaveBalance
    leave_balances = LeaveBalance.query.filter_by(employee_id=id, year=2026).all()
    return render_template('admin/employee_detail.html',
        employee=emp, recent_attendance=recent_attendance,
        recent_leaves=recent_leaves, latest_payroll=latest_payroll,
        leave_balances=leave_balances
    )


@admin_bp.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_employee(id):
    emp = Employee.query.get_or_404(id)
    emp.status = 'terminated'
    if emp.user_account:
        emp.user_account.is_active = False
    db.session.commit()
    flash(f'Employee {emp.full_name} has been terminated.', 'warning')
    return redirect(url_for('admin.employees'))


@admin_bp.route('/departments')
@login_required
@admin_required
def departments():
    departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments)


@admin_bp.route('/departments/add', methods=['POST'])
@login_required
@admin_required
def add_department():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if name:
        dept = Department(name=name, description=description)
        db.session.add(dept)
        db.session.commit()
        flash(f'Department "{name}" added.', 'success')
    return redirect(url_for('admin.departments'))


@admin_bp.route('/departments/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_department(id):
    dept = Department.query.get_or_404(id)
    if dept.employees.count() > 0:
        flash('Cannot delete department with employees.', 'error')
    else:
        db.session.delete(dept)
        db.session.commit()
        flash(f'Department "{dept.name}" deleted.', 'success')
    return redirect(url_for('admin.departments'))


@admin_bp.route('/employees/export')
@login_required
@admin_required
def export_employees():
    employees = Employee.query.all()
    buffer = export_employees_excel(employees)
    return send_file(buffer, as_attachment=True,
                     download_name=f'employees_{date.today().strftime("%Y%m%d")}.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    today = date.today()
    departments = Department.query.all()
    
    return jsonify({
        'dept_names': [d.name for d in departments],
        'dept_counts': [d.employees.filter_by(status='active').count() for d in departments],
        'total_employees': Employee.query.filter_by(status='active').count(),
        'present_today': Attendance.query.filter_by(date=today).filter(
            Attendance.status.in_(['present', 'late'])).count(),
    })
