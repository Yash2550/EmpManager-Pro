from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Employee, Attendance
from utils.decorators import admin_required, hr_required
from utils.qr_generator import generate_qr_base64
from utils.export import export_attendance_excel
from datetime import datetime, date, timedelta
import json

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/qr/<int:emp_id>')
@login_required
def qr_code(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    # Only allow admin/hr or the employee themselves
    if current_user.role == 'employee' and (not current_user.employee_id or current_user.employee_id != emp_id):
        flash('Access denied.', 'error')
        return redirect(url_for('employee.profile'))
    
    qr_data = f"EMPMGMT|{emp.emp_code}|{emp.id}|{emp.full_name}"
    qr_base64 = generate_qr_base64(qr_data)
    
    return render_template('attendance/qr_code.html', employee=emp, qr_base64=qr_base64)


@attendance_bp.route('/scanner')
@login_required
def scanner():
    if current_user.role not in ('admin', 'hr'):
        flash('Access denied.', 'error')
        return redirect(url_for('employee.profile'))
    return render_template('attendance/qr_scanner.html')


@attendance_bp.route('/checkin', methods=['POST'])
@login_required
def checkin():
    data = request.get_json() if request.is_json else None
    
    if data:
        qr_data = data.get('qr_data', '')
    else:
        qr_data = request.form.get('qr_data', '')
    
    # Parse QR data: EMPMGMT|EMP-0001|1|Aarav Sharma
    parts = qr_data.split('|')
    if len(parts) != 4 or parts[0] != 'EMPMGMT':
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
        flash('Invalid QR code.', 'error')
        return redirect(url_for('attendance.scanner'))
    
    emp_code = parts[1]
    emp = Employee.query.filter_by(emp_code=emp_code).first()
    if not emp:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        flash('Employee not found.', 'error')
        return redirect(url_for('attendance.scanner'))
    
    today = date.today()
    existing = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
    
    if existing and existing.check_in:
        if request.is_json:
            return jsonify({'success': False, 'message': f'{emp.full_name} already checked in today'}), 400
        flash(f'{emp.full_name} already checked in today.', 'warning')
        return redirect(url_for('attendance.scanner'))
    
    now = datetime.now()
    status = 'late' if now.hour >= 10 else 'present'
    
    att = Attendance(
        employee_id=emp.id, date=today,
        check_in=now, status=status
    )
    db.session.add(att)
    db.session.commit()
    
    msg = f'{emp.full_name} checked in at {now.strftime("%I:%M %p")} ({status})'
    if request.is_json:
        return jsonify({'success': True, 'message': msg, 'employee': emp.full_name, 'status': status})
    flash(msg, 'success')
    return redirect(url_for('attendance.scanner'))


@attendance_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.get_json() if request.is_json else None
    
    if data:
        qr_data = data.get('qr_data', '')
    else:
        qr_data = request.form.get('qr_data', '')
    
    parts = qr_data.split('|')
    if len(parts) != 4 or parts[0] != 'EMPMGMT':
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
        flash('Invalid QR code.', 'error')
        return redirect(url_for('attendance.scanner'))
    
    emp_code = parts[1]
    emp = Employee.query.filter_by(emp_code=emp_code).first()
    if not emp:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Employee not found'}), 404
        flash('Employee not found.', 'error')
        return redirect(url_for('attendance.scanner'))
    
    today = date.today()
    att = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
    
    if not att or not att.check_in:
        if request.is_json:
            return jsonify({'success': False, 'message': f'{emp.full_name} has not checked in today'}), 400
        flash(f'{emp.full_name} has not checked in today.', 'warning')
        return redirect(url_for('attendance.scanner'))
    
    if att.check_out:
        if request.is_json:
            return jsonify({'success': False, 'message': f'{emp.full_name} already checked out'}), 400
        flash(f'{emp.full_name} already checked out.', 'warning')
        return redirect(url_for('attendance.scanner'))
    
    now = datetime.now()
    att.check_out = now
    att.hours_worked = round((now - att.check_in).total_seconds() / 3600, 1)
    db.session.commit()
    
    msg = f'{emp.full_name} checked out at {now.strftime("%I:%M %p")} — {att.hours_worked}h worked'
    if request.is_json:
        return jsonify({'success': True, 'message': msg, 'hours': att.hours_worked})
    flash(msg, 'success')
    return redirect(url_for('attendance.scanner'))


@attendance_bp.route('/report')
@login_required
def report():
    if current_user.role not in ('admin', 'hr'):
        flash('Access denied.', 'error')
        return redirect(url_for('employee.profile'))
    
    start = request.args.get('start', (date.today() - timedelta(days=30)).isoformat())
    end = request.args.get('end', date.today().isoformat())
    emp_filter = request.args.get('employee', '', type=str)
    
    start_date = datetime.strptime(start, '%Y-%m-%d').date()
    end_date = datetime.strptime(end, '%Y-%m-%d').date()
    
    query = Attendance.query.filter(Attendance.date.between(start_date, end_date))
    if emp_filter:
        query = query.filter_by(employee_id=int(emp_filter))
    
    records = query.order_by(Attendance.date.desc(), Attendance.employee_id).all()
    employees = Employee.query.filter_by(status='active').order_by(Employee.first_name).all()
    
    # Stats
    total_records = len(records)
    present_count = sum(1 for r in records if r.status in ('present', 'late'))
    absent_count = sum(1 for r in records if r.status == 'absent')
    late_count = sum(1 for r in records if r.status == 'late')
    avg_hours = round(sum(r.hours_worked or 0 for r in records) / max(present_count, 1), 1)
    
    return render_template('attendance/attendance_report.html',
        records=records, employees=employees,
        start=start, end=end, emp_filter=emp_filter,
        total_records=total_records, present_count=present_count,
        absent_count=absent_count, late_count=late_count, avg_hours=avg_hours
    )


@attendance_bp.route('/report/export')
@login_required
def export_report():
    if current_user.role not in ('admin', 'hr'):
        flash('Access denied.', 'error')
        return redirect(url_for('employee.profile'))
    
    start = request.args.get('start', (date.today() - timedelta(days=30)).isoformat())
    end = request.args.get('end', date.today().isoformat())
    start_date = datetime.strptime(start, '%Y-%m-%d').date()
    end_date = datetime.strptime(end, '%Y-%m-%d').date()
    
    records = Attendance.query.filter(Attendance.date.between(start_date, end_date)).order_by(Attendance.date.desc()).all()
    buffer = export_attendance_excel(records)
    return send_file(buffer, as_attachment=True,
                     download_name=f'attendance_{start}_{end}.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@attendance_bp.route('/my')
@login_required
def my_attendance():
    if not current_user.employee_id:
        flash('No employee profile linked.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)
    
    records = Attendance.query.filter_by(employee_id=current_user.employee_id).filter(
        Attendance.date.between(start_date, end_date)
    ).order_by(Attendance.date).all()
    
    present = sum(1 for r in records if r.status in ('present', 'late'))
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')
    total_hours = round(sum(r.hours_worked or 0 for r in records), 1)
    
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    return render_template('attendance/my_attendance.html',
        records=records, month=month, year=year, months=months,
        present=present, absent=absent, late=late, total_hours=total_hours
    )
