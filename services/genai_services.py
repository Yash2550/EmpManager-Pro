"""
GenAI Services — AI-powered org health reports and performance insights.
Employee-facing analytics.
"""
from datetime import date, datetime


def generate_org_health_report() -> tuple:
    """Generate an AI health report about the organization for the employee dashboard."""
    try:
        from models import Employee, LeaveRequest, Performance, Payroll
        from sqlalchemy import func
        from models import db

        total = Employee.query.filter_by(status='active').count()
        if total == 0:
            return "No employee data available.", 0

        pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
        avg_rating = db.session.query(func.avg(Performance.rating)).scalar() or 0
        this_month = date.today()
        payroll_sum = db.session.query(func.sum(Payroll.net_salary)).filter_by(
            month=this_month.month, year=this_month.year
        ).scalar() or 0

        score = min(100, int(
            (avg_rating / 5.0) * 40 +
            max(0, (1 - pending_leaves / max(total, 1)) * 30) +
            30
        ))

        report_lines = [
            f"**Organization Health Score: {score}/100**",
            "",
            f"- 👥 Active Employees: **{total}**",
            f"- ⭐ Average Performance Rating: **{avg_rating:.1f}/5**",
            f"- 📋 Pending Leave Requests: **{pending_leaves}**",
            f"- 💰 Monthly Payroll: **₹{payroll_sum:,.0f}**",
            "",
            _health_comment(score)
        ]

        return "\n".join(report_lines), score

    except Exception as e:
        return f"Unable to generate report: {str(e)}", 0


def _health_comment(score: int) -> str:
    if score >= 80:
        return "✅ The organization is in excellent health with strong performance metrics."
    elif score >= 60:
        return "🟡 The organization is performing well, with some areas for improvement."
    else:
        return "🔴 There are some concerns that need HR attention. Review pending leaves and performance reviews."


def generate_payroll_insights() -> str:
    """Generate payroll trend insights for the current employee."""
    try:
        from models import Payroll, db
        from sqlalchemy import func
        import calendar

        today = date.today()
        insights = []

        for offset in range(3):
            m = today.month - offset
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            total = db.session.query(func.sum(Payroll.net_salary)).filter_by(month=m, year=y).scalar() or 0
            count = Payroll.query.filter_by(month=m, year=y).count()
            avg = total / count if count else 0
            insights.append(f"**{calendar.month_name[m]} {y}**: Total ₹{total:,.0f} | Avg ₹{avg:,.0f} | {count} employees paid")

        return "\n".join(insights) if insights else "No payroll data available."
    except Exception as e:
        return f"Payroll data unavailable: {str(e)}"


def generate_performance_summary(emp_id: int) -> str:
    """Generate a natural-language performance summary for an employee."""
    try:
        from models import Performance, Employee
        emp = Employee.query.get(emp_id)
        if not emp:
            return "Employee not found."

        reviews = Performance.query.filter_by(employee_id=emp_id).order_by(
            Performance.review_date.desc()
        ).limit(3).all()

        if not reviews:
            return f"No performance reviews found for {emp.full_name}."

        lines = [f"**Performance Summary for {emp.full_name}**", ""]
        for r in reviews:
            pct = int((r.goals_met / r.goals_total * 100)) if r.goals_total else 0
            lines.append(f"**{r.period}** — Rating: {r.rating}/5 | Goals: {r.goals_met}/{r.goals_total} ({pct}%)")
            if r.strengths:
                lines.append(f"  💪 Strengths: {r.strengths}")
            if r.improvements:
                lines.append(f"  📈 Improvements: {r.improvements}")
            lines.append("")

        avg = sum(r.rating for r in reviews) / len(reviews)
        trend = "📈 improving" if len(reviews) > 1 and reviews[0].rating > reviews[-1].rating else "📊 stable"
        lines.append(f"Average rating: **{avg:.1f}/5** — Trend: {trend}")

        return "\n".join(lines)
    except Exception as e:
        return f"Unable to generate summary: {str(e)}"


def generate_leave_recommendation(leave_id: int) -> str:
    """Provide a simple recommendation for a leave request."""
    try:
        from models import LeaveRequest, LeaveBalance, Employee
        leave = LeaveRequest.query.get(leave_id)
        if not leave:
            return "Leave request not found."

        balance = LeaveBalance.query.filter_by(
            employee_id=leave.employee_id,
            leave_type=leave.leave_type,
            year=date.today().year
        ).first()

        emp = Employee.query.get(leave.employee_id)
        name = emp.full_name if emp else "Employee"

        if not balance:
            return f"⚠️ No leave balance record found for {name}. Review manually."

        if leave.days > balance.remaining:
            return f"❌ **Recommend Rejection**: {name} only has {balance.remaining} {leave.leave_type} days remaining, but requested {leave.days} days."
        elif leave.days <= 2:
            return f"✅ **Recommend Approval**: Short leave ({leave.days} days) with sufficient balance ({balance.remaining} days remaining)."
        elif balance.remaining >= leave.days * 2:
            return f"✅ **Recommend Approval**: {name} has ample leave balance ({balance.remaining} days remaining)."
        else:
            return f"🟡 **Review Recommended**: {name} requests {leave.days} days with {balance.remaining} days remaining. Use discretion."

    except Exception as e:
        return f"Unable to generate recommendation: {str(e)}"
