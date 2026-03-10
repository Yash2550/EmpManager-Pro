from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, Employee, LeaveRequest, LeaveBalance, Payroll, Performance, Notification, User
from utils.decorators import hr_required
from utils.export import export_payroll_excel
from datetime import datetime, date
import calendar

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')


@hr_bp.route('/leaves')
@login_required
@hr_required
def leave_management():
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = LeaveRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    leaves = query.order_by(LeaveRequest.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    
    pending_count = LeaveRequest.query.filter_by(status='pending').count()
    approved_count = LeaveRequest.query.filter_by(status='approved').count()
    rejected_count = LeaveRequest.query.filter_by(status='rejected').count()
    
    return render_template('hr/leave_management.html',
        leaves=leaves, status_filter=status_filter,
        pending_count=pending_count, approved_count=approved_count,
        rejected_count=rejected_count
    )


@hr_bp.route('/leaves/approve/<int:id>', methods=['POST'])
@login_required
@hr_required
def approve_leave(id):
    leave = LeaveRequest.query.get_or_404(id)
    action = request.form.get('action', 'approve')
    
    if action == 'approve':
        leave.status = 'approved'
        leave.approved_by = current_user.id
        leave.approved_at = datetime.utcnow()
        
        # Update leave balance
        balance = LeaveBalance.query.filter_by(
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            year=2026
        ).first()
        if balance:
            balance.used += leave.days
            balance.remaining = balance.total - balance.used
        
        # Notify employee
        emp_user = User.query.filter_by(employee_id=leave.employee_id).first()
        if emp_user:
            notif = Notification(
                user_id=emp_user.id,
                title='Leave Approved',
                message=f'Your {leave.leave_type} leave from {leave.start_date} to {leave.end_date} has been approved.',
                type='success'
            )
            db.session.add(notif)
        
        flash('Leave request approved.', 'success')
    else:
        leave.status = 'rejected'
        leave.approved_by = current_user.id
        leave.approved_at = datetime.utcnow()
        leave.rejection_reason = request.form.get('reason', '')
        
        emp_user = User.query.filter_by(employee_id=leave.employee_id).first()
        if emp_user:
            notif = Notification(
                user_id=emp_user.id,
                title='Leave Rejected',
                message=f'Your {leave.leave_type} leave request has been rejected.',
                type='error'
            )
            db.session.add(notif)
        
        flash('Leave request rejected.', 'warning')
    
    db.session.commit()
    return redirect(url_for('hr.leave_management'))


@hr_bp.route('/payroll')
@login_required
@hr_required
def payroll():
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    payrolls = Payroll.query.filter_by(month=month, year=year).order_by(Payroll.employee_id).all()
    
    total_gross = sum(p.gross_salary for p in payrolls)
    total_deductions = sum(p.pf_deduction + p.tax_deduction + p.other_deductions for p in payrolls)
    total_net = sum(p.net_salary for p in payrolls)
    
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(2024, 2028))
    
    return render_template('hr/payroll.html',
        payrolls=payrolls, month=month, year=year,
        months=months, years=years,
        total_gross=total_gross, total_deductions=total_deductions, total_net=total_net
    )


@hr_bp.route('/payroll/generate', methods=['POST'])
@login_required
@hr_required
def generate_payroll():
    month = int(request.form.get('month', date.today().month))
    year = int(request.form.get('year', date.today().year))
    
    # Check if already generated
    existing = Payroll.query.filter_by(month=month, year=year).count()
    if existing > 0:
        flash(f'Payroll for {calendar.month_name[month]} {year} already exists.', 'warning')
        return redirect(url_for('hr.payroll', month=month, year=year))
    
    employees = Employee.query.filter_by(status='active').all()
    count = 0
    for emp in employees:
        basic = emp.salary
        hra = round(basic * 0.40, 2)
        da = round(basic * 0.10, 2)
        ta = round(basic * 0.05, 2)
        gross = basic + hra + da + ta
        pf = round(basic * 0.12, 2)
        tax = round(gross * 0.10, 2) if gross > 50000 else 0
        net = round(gross - pf - tax, 2)
        
        p = Payroll(
            employee_id=emp.id, month=month, year=year,
            basic_salary=basic, hra=hra, da=da, ta=ta,
            pf_deduction=pf, tax_deduction=tax,
            gross_salary=gross, net_salary=net,
            status='generated'
        )
        db.session.add(p)
        count += 1
    
    db.session.commit()
    flash(f'Payroll generated for {count} employees.', 'success')
    return redirect(url_for('hr.payroll', month=month, year=year))


@hr_bp.route('/payroll/export')
@login_required
@hr_required
def export_payroll():
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    payrolls = Payroll.query.filter_by(month=month, year=year).all()
    buffer = export_payroll_excel(payrolls)
    return send_file(buffer, as_attachment=True,
                     download_name=f'payroll_{calendar.month_name[month]}_{year}.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@hr_bp.route('/performance')
@login_required
@hr_required
def performance():
    period = request.args.get('period', '')
    query = Performance.query
    if period:
        query = query.filter_by(period=period)
    
    reviews = query.order_by(Performance.review_date.desc()).all()
    
    # Available periods
    periods = db.session.query(Performance.period).distinct().all()
    periods = [p[0] for p in periods]
    
    avg_rating = db.session.query(db.func.avg(Performance.rating)).scalar() or 0
    
    return render_template('hr/performance.html',
        reviews=reviews, periods=periods, period=period, avg_rating=round(avg_rating, 1)
    )


@hr_bp.route('/performance/add', methods=['GET', 'POST'])
@login_required
@hr_required
def add_performance():
    if request.method == 'POST':
        review = Performance(
            employee_id=int(request.form['employee_id']),
            reviewer_id=int(request.form.get('reviewer_id', 0)) or None,
            period=request.form['period'],
            rating=float(request.form.get('rating', 0)),
            goals_met=int(request.form.get('goals_met', 0)),
            goals_total=int(request.form.get('goals_total', 0)),
            strengths=request.form.get('strengths', ''),
            improvements=request.form.get('improvements', ''),
            comments=request.form.get('comments', ''),
            review_date=date.today()
        )
        db.session.add(review)
        
        # Notify employee
        emp_user = User.query.filter_by(employee_id=review.employee_id).first()
        if emp_user:
            notif = Notification(
                user_id=emp_user.id,
                title='Performance Review',
                message=f'A new performance review for {review.period} has been added.',
                type='info'
            )
            db.session.add(notif)
        
        db.session.commit()
        flash('Performance review added.', 'success')
        return redirect(url_for('hr.performance'))
    
    employees = Employee.query.filter_by(status='active').all()
    return render_template('hr/performance_form.html', employees=employees)
