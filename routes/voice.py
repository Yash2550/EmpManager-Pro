"""
Voice Agent Routes — Twilio outbound calling (Employee only).
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.decorators import role_required
from models import db, Employee

voice_bp = Blueprint('voice', __name__, url_prefix='/voice')


@voice_bp.route('/agent')
@login_required
@role_required('employee', 'hr')
def voice_agent():
    """Voice agent page (employee only)."""
    emp = None
    if current_user.employee_id:
        emp = Employee.query.get(current_user.employee_id)
    from services.voice_service import get_predefined_messages
    messages = get_predefined_messages()
    return render_template('ai/voice_agent.html', employee=emp, predefined_messages=messages)


@voice_bp.route('/call', methods=['POST'])
@login_required
@role_required('employee', 'hr')
def make_call():
    """Initiate a Twilio voice call."""
    from services.voice_service import make_voice_call

    data = request.get_json() or {}
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()
    emp_name = 'Employee'

    if current_user.employee_id:
        emp = Employee.query.get(current_user.employee_id)
        if emp:
            emp_name = emp.full_name

    if not phone:
        return jsonify({'success': False, 'error': 'Phone number is required'})
    if not message:
        return jsonify({'success': False, 'error': 'Message is required'})

    result = make_voice_call(to_phone=phone, message=message, employee_name=emp_name)
    return jsonify(result)


@voice_bp.route('/status/<call_sid>')
@login_required
@role_required('employee')
def call_status(call_sid):
    """Check status of a voice call."""
    from services.voice_service import get_call_status
    status = get_call_status(call_sid)
    return jsonify(status)
