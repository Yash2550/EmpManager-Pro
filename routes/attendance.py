from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Employee, Attendance
from datetime import datetime, date
import calendar

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/checkin', methods=['POST'])
@login_required
def checkin():
    """Button-based check-in."""
    if not current_user.employee_id:
        return jsonify({'error': 'No employee profile linked'}), 400
        
    today = date.today()
    existing = Attendance.query.filter_by(employee_id=current_user.employee_id, date=today).first()
    
    if existing and existing.check_in:
        flash('You have already checked in today.', 'info')
        return redirect(url_for('attendance.my_attendance'))
        
    now = datetime.now().time()
    
    if existing:
        existing.check_in = now
        existing.status = 'present'
    else:
        new_attendance = Attendance(
            employee_id=current_user.employee_id,
            date=today,
            check_in=now,
            status='present'
        )
        db.session.add(new_attendance)
        
    db.session.commit()
    flash('Successfully checked in!', 'success')
    return redirect(url_for('attendance.my_attendance'))


@attendance_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Button-based check-out."""
    if not current_user.employee_id:
        return jsonify({'error': 'No employee profile linked'}), 400
        
    today = date.today()
    attendance = Attendance.query.filter_by(employee_id=current_user.employee_id, date=today).first()
    
    if not attendance or not attendance.check_in:
        flash('You need to check in first.', 'warning')
        return redirect(url_for('attendance.my_attendance'))
        
    if attendance.check_out:
        flash('You have already checked out today.', 'info')
        return redirect(url_for('attendance.my_attendance'))
        
    attendance.check_out = datetime.now().time()
    db.session.commit()
    
    flash('Successfully checked out!', 'success')
    return redirect(url_for('attendance.my_attendance'))


@attendance_bp.route('/my_attendance')
@login_required
def my_attendance():
    """View personal attendance records."""
    if not current_user.employee_id:
        flash('No employee profile linked.', 'warning')
        return redirect(url_for('employee.profile'))
        
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    records = Attendance.query.filter(
        Attendance.employee_id == current_user.employee_id,
        db.extract('month', Attendance.date) == month,
        db.extract('year', Attendance.date) == year
    ).order_by(Attendance.date.desc()).all()
    
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    # Check if already checked in today
    today = date.today()
    today_attendance = Attendance.query.filter_by(employee_id=current_user.employee_id, date=today).first()
    
    is_checked_in = bool(today_attendance and today_attendance.check_in)
    is_checked_out = bool(today_attendance and today_attendance.check_out)
    
    return render_template('attendance/my_attendance.html', 
        records=records, 
        month=month, 
        year=year, 
        months=months,
        is_checked_in=is_checked_in,
        is_checked_out=is_checked_out
    )


@attendance_bp.route('/report')
@login_required
def report():
    """Admin/HR attendance report."""
    if current_user.role not in ['admin', 'hr']:
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
        
    target_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        query_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        query_date = date.today()
        
    records = Attendance.query.filter_by(date=query_date).all()
    
    return render_template('attendance/report.html', records=records, date=query_date)


@attendance_bp.route('/report/export')
@login_required
def export_report():
    """Export attendance to Excel/CSV."""
    if current_user.role not in ['admin', 'hr']:
        return jsonify({'error': 'Access denied'}), 403
    # Stub for export functionality
    flash('Export feature coming soon.', 'info')
    return redirect(url_for('attendance.report'))
