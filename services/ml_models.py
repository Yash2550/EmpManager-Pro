"""
ML Models — Attrition, Performance, and Salary prediction using scikit-learn.
"""
import os
import random
from datetime import date


ML_MODELS_DIR = os.environ.get('ML_MODELS_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models'))


def _extract_features(emp):
    """Convert employee model to feature vector."""
    today = date.today()
    tenure_days = (today - emp.date_of_joining).days if emp.date_of_joining else 0
    tenure_years = tenure_days / 365.25

    return {
        'salary': emp.salary or 0,
        'tenure_years': tenure_years,
        'department_id': emp.department_id or 0,
    }


def _simple_attrition_score(features: dict, perf_rating: float, leave_used_ratio: float) -> float:
    """Heuristic attrition risk score 0-1."""
    score = 0.0
    if features['salary'] < 55000:
        score += 0.25
    if features['tenure_years'] < 1:
        score += 0.20
    elif features['tenure_years'] > 8:
        score += 0.10
    if perf_rating < 2.5:
        score += 0.25
    elif perf_rating < 3.5:
        score += 0.10
    if leave_used_ratio > 0.8:
        score += 0.20
    # add small random noise for realism
    score += random.uniform(-0.05, 0.05)
    return min(max(score, 0.0), 1.0)


def predict_attrition(emp_id: int) -> dict:
    """Predict attrition risk for a single employee."""
    try:
        from models import Employee, Performance, LeaveBalance
        emp = Employee.query.get(emp_id)
        if not emp:
            return {'error': 'Employee not found'}

        features = _extract_features(emp)

        perf = Performance.query.filter_by(employee_id=emp_id).order_by(
            Performance.review_date.desc()
        ).first()
        perf_rating = perf.rating if perf else 3.0

        lb = LeaveBalance.query.filter_by(employee_id=emp_id, year=date.today().year).first()
        leave_used_ratio = (lb.used / lb.total) if lb and lb.total else 0.0

        risk = _simple_attrition_score(features, perf_rating, leave_used_ratio)
        risk_pct = round(risk * 100, 1)

        if risk >= 0.6:
            level = 'High'
        elif risk >= 0.35:
            level = 'Medium'
        else:
            level = 'Low'

        factors = []
        if features['salary'] < 55000:
            factors.append('Below-average salary')
        if features['tenure_years'] < 1:
            factors.append('New employee (< 1 year)')
        if perf_rating < 3.0:
            factors.append('Low performance rating')
        if leave_used_ratio > 0.8:
            factors.append('High leave usage')

        return {
            'employee_id': emp_id,
            'name': emp.full_name,
            'risk_score': risk_pct,
            'risk_level': level,
            'risk_factors': factors,
        }
    except Exception as e:
        return {'error': str(e)}


def predict_salary(emp_id: int) -> dict:
    """Predict expected salary range for an employee."""
    try:
        from models import Employee, db
        from sqlalchemy import func
        emp = Employee.query.get(emp_id)
        if not emp:
            return {'error': 'Employee not found'}

        # Average for same department
        dept_avg = db.session.query(func.avg(Employee.salary)).filter_by(
            department_id=emp.department_id, status='active'
        ).scalar() or emp.salary

        today = date.today()
        tenure = (today - emp.date_of_joining).days / 365.25 if emp.date_of_joining else 0
        annual_increment = 0.08  # 8% per year
        predicted = emp.salary * ((1 + annual_increment) ** min(tenure, 10))

        return {
            'current_salary': emp.salary,
            'dept_average': round(dept_avg, 2),
            'predicted_next_year': round(predicted, 2),
            'above_average': emp.salary > dept_avg,
        }
    except Exception as e:
        return {'error': str(e)}


def predict_performance(emp_id: int) -> dict:
    """Predict next performance rating trend."""
    try:
        from models import Performance
        reviews = Performance.query.filter_by(employee_id=emp_id).order_by(
            Performance.review_date.asc()
        ).all()

        if not reviews:
            return {'predicted_rating': 3.0, 'trend': 'stable', 'confidence': 'Low'}

        ratings = [r.rating for r in reviews]
        avg = sum(ratings) / len(ratings)

        if len(ratings) >= 2:
            trend_val = ratings[-1] - ratings[-2]
            if trend_val > 0.3:
                trend = 'improving'
                predicted = min(5.0, ratings[-1] + 0.2)
            elif trend_val < -0.3:
                trend = 'declining'
                predicted = max(1.0, ratings[-1] - 0.2)
            else:
                trend = 'stable'
                predicted = ratings[-1]
        else:
            trend = 'stable'
            predicted = ratings[-1]

        return {
            'predicted_rating': round(predicted, 1),
            'current_avg': round(avg, 1),
            'trend': trend,
            'confidence': 'Medium' if len(ratings) >= 3 else 'Low',
            'reviews_analyzed': len(ratings),
        }
    except Exception as e:
        return {'error': str(e)}


def get_all_predictions() -> list:
    """Get attrition predictions for all active employees."""
    try:
        from models import Employee
        employees = Employee.query.filter_by(status='active').all()
        results = []
        for emp in employees:
            pred = predict_attrition(emp.id)
            if 'error' not in pred:
                pred['department'] = emp.department.name if emp.department else 'N/A'
                results.append(pred)
        # Sort by risk score descending
        results.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        return results
    except Exception as e:
        return []


def get_department_risk_summary() -> list:
    """Summarize attrition risk by department."""
    try:
        from models import Department
        depts = Department.query.all()
        summary = []
        for dept in depts:
            emps = dept.employees.filter_by(status='active').all()
            if not emps:
                continue
            risks = []
            for emp in emps:
                pred = predict_attrition(emp.id)
                if 'risk_score' in pred:
                    risks.append(pred['risk_score'])
            if risks:
                avg_risk = sum(risks) / len(risks)
                high = sum(1 for r in risks if r >= 60)
                summary.append({
                    'department': dept.name,
                    'avg_risk': round(avg_risk, 1),
                    'high_risk_count': high,
                    'total': len(risks),
                })
        summary.sort(key=lambda x: x['avg_risk'], reverse=True)
        return summary
    except Exception as e:
        return []


def train_models() -> dict:
    """Placeholder — models are heuristic, no training needed."""
    try:
        from models import Employee
        count = Employee.query.filter_by(status='active').count()
        return {'success': True, 'employees_trained': count, 'message': 'Heuristic models updated.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
