"""
ML Prediction Routes — Employee-only ML analytics.
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.ml_models import (
    predict_attrition, predict_salary,
    predict_performance, get_all_predictions, get_department_risk_summary
)

ml_bp = Blueprint('ml', __name__, url_prefix='/ml')


@ml_bp.route('/dashboard')
@login_required
@role_required('employee', 'hr')
def dashboard():
    """ML predictions dashboard (employee only)."""
    predictions = get_all_predictions()
    dept_summary = get_department_risk_summary()

    high_risk = [p for p in predictions if p['risk_level'] == 'High']
    medium_risk = [p for p in predictions if p['risk_level'] == 'Medium']
    low_risk = [p for p in predictions if p['risk_level'] == 'Low']

    return render_template('ml/ml_dashboard.html',
        predictions=predictions,
        dept_summary=dept_summary,
        high_risk=high_risk,
        medium_risk=medium_risk,
        low_risk=low_risk,
        total=len(predictions)
    )


@ml_bp.route('/predict/<int:emp_id>')
@login_required
@role_required('employee', 'hr')
def employee_prediction(emp_id):
    """Get all predictions for a single employee."""
    attrition = predict_attrition(emp_id)
    salary = predict_salary(emp_id)
    performance = predict_performance(emp_id)

    return jsonify({
        'attrition': attrition,
        'salary': salary,
        'performance': performance
    })


@ml_bp.route('/my-predictions')
@login_required
@role_required('employee', 'hr')
def my_predictions():
    """Get predictions for the currently logged-in employee."""
    if not current_user.employee_id:
        return jsonify({'error': 'No employee profile linked'})

    return jsonify({
        'attrition': predict_attrition(current_user.employee_id),
        'salary': predict_salary(current_user.employee_id),
        'performance': predict_performance(current_user.employee_id)
    })


@ml_bp.route('/department-risks')
@login_required
@role_required('employee', 'hr')
def department_risks():
    """Get department risk summary."""
    summary = get_department_risk_summary()
    return jsonify({'departments': summary})
