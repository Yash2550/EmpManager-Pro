from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Employee, LeaveRequest, LeaveBalance, Payroll, Notification, Attendance
from datetime import datetime, date
import calendar

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.route('/profile')
@login_required
def profile():
    emp = None
    if current_user.employee_id:
        emp = Employee.query.get(current_user.employee_id)
    
    # Unread notifications count
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # Today's attendance
    today_att = None
    if emp:
        today_att = Attendance.query.filter_by(employee_id=emp.id, date=date.today()).first()
    
    return render_template('employee/profile.html', employee=emp, unread=unread, today_att=today_att)


@employee_bp.route('/leave/request', methods=['GET', 'POST'])
@login_required
def leave_request():
    if not current_user.employee_id:
        flash('No employee profile linked.', 'warning')
        return redirect(url_for('employee.profile'))
    
    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        reason = request.form.get('reason', '')
        
        if end_date < start_date:
            flash('End date must be after start date.', 'error')
            return redirect(url_for('employee.leave_request'))
        
        days = (end_date - start_date).days + 1
        
        # Check balance
        balance = LeaveBalance.query.filter_by(
            employee_id=current_user.employee_id,
            leave_type=leave_type, year=2026
        ).first()
        
        if balance and days > balance.remaining:
            flash(f'Insufficient {leave_type} leave balance. Available: {balance.remaining} days.', 'error')
            return redirect(url_for('employee.leave_request'))
        
        lr = LeaveRequest(
            employee_id=current_user.employee_id,
            leave_type=leave_type,
            start_date=start_date, end_date=end_date,
            days=days, reason=reason, status='pending'
        )
        db.session.add(lr)
        db.session.commit()
        
        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('employee.leaves'))
    
    balances = LeaveBalance.query.filter_by(employee_id=current_user.employee_id, year=2026).all()
    return render_template('employee/leave_request.html', balances=balances)


@employee_bp.route('/leaves')
@login_required
def leaves():
    if not current_user.employee_id:
        flash('No employee profile linked.', 'warning')
        return redirect(url_for('employee.profile'))
    
    leave_reqs = LeaveRequest.query.filter_by(employee_id=current_user.employee_id).order_by(
        LeaveRequest.created_at.desc()
    ).all()
    
    balances = LeaveBalance.query.filter_by(employee_id=current_user.employee_id, year=2026).all()
    
    return render_template('employee/leaves.html', leave_requests=leave_reqs, balances=balances)


@employee_bp.route('/payslip')
@login_required
def payslip():
    if not current_user.employee_id:
        flash('No employee profile linked.', 'warning')
        return redirect(url_for('employee.profile'))
    
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    payslip = Payroll.query.filter_by(
        employee_id=current_user.employee_id, month=month, year=year
    ).first()
    
    emp = Employee.query.get(current_user.employee_id)
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    
    return render_template('employee/payslip.html',
        payslip=payslip, employee=emp, month=month, year=year, months=months
    )


@employee_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return render_template('employee/notifications.html', notifications=notifs)


@employee_bp.route('/notifications/count')
@login_required
def notification_count():
    from flask import jsonify
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
