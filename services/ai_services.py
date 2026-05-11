"""
AI Services — RAG-powered chatbot using Groq/Llama3.
Accessible to employee role only.
"""
import os
from datetime import datetime

# ─── Groq RAG Chatbot ─────────────────────────────────────────

def _get_groq_client():
    try:
        from groq import Groq
        api_key = os.environ.get('GROQ_API_KEY', '')
        return Groq(api_key=api_key)
    except Exception:
        return None


def _build_context(user_role: str, employee_id=None) -> str:
    """Gather relevant data from the DB to use as RAG context."""
    from models import db, Employee, LeaveRequest, LeaveBalance, Payroll, Performance
    from datetime import date

    ctx_parts = []

    # If employee, fetch their own data
    if employee_id:
        emp = Employee.query.get(employee_id)
        if emp:
            ctx_parts.append(f"Employee: {emp.full_name} ({emp.emp_code}), Dept: {emp.department.name if emp.department else 'N/A'}, Role: {emp.designation}, Salary: ₹{emp.salary:,.0f}, Status: {emp.status}")

            # Leave balances
            balances = LeaveBalance.query.filter_by(employee_id=employee_id, year=date.today().year).all()
            for b in balances:
                ctx_parts.append(f"Leave balance ({b.leave_type}): {b.remaining}/{b.total} days remaining")

            # Recent leave requests
            leaves = LeaveRequest.query.filter_by(employee_id=employee_id).order_by(LeaveRequest.created_at.desc()).limit(5).all()
            for l in leaves:
                ctx_parts.append(f"Leave request: {l.leave_type} from {l.start_date} to {l.end_date}, status={l.status}")

            # Latest payslip
            payroll = Payroll.query.filter_by(employee_id=employee_id).order_by(Payroll.year.desc(), Payroll.month.desc()).first()
            if payroll:
                import calendar
                ctx_parts.append(f"Latest payslip ({calendar.month_name[payroll.month]} {payroll.year}): Gross=₹{payroll.gross_salary:,.0f}, Net=₹{payroll.net_salary:,.0f}, Status={payroll.status}")

            # Latest performance review
            perf = Performance.query.filter_by(employee_id=employee_id).order_by(Performance.review_date.desc()).first()
            if perf:
                ctx_parts.append(f"Last performance review ({perf.period}): Rating={perf.rating}/5, Goals met={perf.goals_met}/{perf.goals_total}")

    return "\n".join(ctx_parts)


def chat_with_rag(user_message: str, user_id: int, user_role: str, employee_id=None) -> str:
    """Send message to Groq LLM with RAG context from the database."""
    client = _get_groq_client()
    if not client:
        return _fallback_response(user_message, user_role, employee_id)

    context = _build_context(user_role, employee_id)

    system_prompt = f"""You are EmpManager AI, a friendly and helpful HR assistant for employees.
You have access to the following real-time data about this employee:

{context}

Guidelines:
- Answer HR-related questions about leaves, payroll, attendance, performance, and company policies.
- Be concise, accurate, and professional.
- If data is available in the context, use it to give specific answers.
- If something is outside your scope, politely say so.
- Current date: {datetime.now().strftime('%d %B %Y')}
"""

    try:
        # Get recent chat history for multi-turn context
        from models import ChatMessage
        history = ChatMessage.query.filter_by(user_id=user_id).order_by(
            ChatMessage.created_at.asc()
        ).limit(10).all()

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-8:]:  # last 8 messages for context
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=os.environ.get('GROQ_MODEL', 'llama3-8b-8192'),
            messages=messages,
            max_tokens=600,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return _fallback_response(user_message, user_role, employee_id)


def _fallback_response(user_message: str, user_role: str, employee_id=None) -> str:
    """Simple rule-based fallback when AI is unavailable."""
    msg = user_message.lower()
    if any(w in msg for w in ['leave', 'vacation', 'holiday', 'day off']):
        return "You can check your leave balance and request leaves from the **My Leaves** section in the sidebar. Contact HR if you need further assistance."
    if any(w in msg for w in ['pay', 'salary', 'payslip', 'slip']):
        return "Your payslip is available in the **My Payslip** section. It shows your basic, HRA, DA, deductions, and net salary."
    if any(w in msg for w in ['performance', 'review', 'rating', 'goal']):
        return "Your performance reviews are managed by HR. You'll receive a notification when a new review is added."
    if any(w in msg for w in ['attendance', 'clock', 'check in', 'check out']):
        return "You can view your attendance records in the **My Attendance** section."
    if any(w in msg for w in ['hello', 'hi', 'hey', 'help']):
        return "👋 Hello! I'm your EmpManager AI assistant. I can help you with leaves, payroll, attendance, and performance queries. What would you like to know?"
    return "I'm here to help with HR-related questions! Ask me about your leaves, payslip, attendance, or performance reviews."
