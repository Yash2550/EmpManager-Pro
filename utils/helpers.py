from datetime import datetime, date, timedelta
import calendar


def format_date(d, fmt='%d %b %Y'):
    """Format a date object to a display string."""
    if isinstance(d, str):
        d = datetime.strptime(d, '%Y-%m-%d').date()
    if d is None:
        return 'N/A'
    return d.strftime(fmt)


def format_datetime(dt, fmt='%d %b %Y, %I:%M %p'):
    """Format a datetime object."""
    if dt is None:
        return 'N/A'
    return dt.strftime(fmt)


def format_currency(amount):
    """Format a number as Indian currency."""
    if amount is None:
        return '₹0.00'
    return f'₹{amount:,.2f}'


def get_month_name(month_number):
    """Get month name from number (1-12)."""
    return calendar.month_name[month_number]


def calculate_working_days(start_date, end_date):
    """Calculate working days between two dates (excluding weekends)."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    working_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Mon-Fri
            working_days += 1
        current += timedelta(days=1)
    return working_days


def get_leave_days(start_date, end_date):
    """Calculate leave days between two dates (inclusive)."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    return (end_date - start_date).days + 1


def generate_emp_code(dept_prefix, employee_id):
    """Generate an employee code like EMP-IT-001."""
    return f"EMP-{dept_prefix}-{employee_id:03d}"


def get_current_quarter():
    """Get the current quarter string, e.g. Q1-2026."""
    month = datetime.now().month
    quarter = (month - 1) // 3 + 1
    return f"Q{quarter}-{datetime.now().year}"


def time_since(dt):
    """Return a human-readable time-since string."""
    if dt is None:
        return 'N/A'
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    if diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return 'Just now'
