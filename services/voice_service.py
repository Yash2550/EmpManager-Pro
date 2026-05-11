"""
Voice Service — Twilio-powered outbound voice agent.
"""
import os


def make_voice_call(to_phone: str, message: str, employee_name: str = 'Employee') -> dict:
    """Make an outbound Twilio call with a TTS message."""
    try:
        from twilio.rest import Client
        from flask import current_app
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID') or os.environ.get('TWILIO_ACCOUNT_SID', '')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN') or os.environ.get('TWILIO_AUTH_TOKEN', '')
        from_number = current_app.config.get('TWILIO_PHONE_NUMBER') or os.environ.get('TWILIO_PHONE_NUMBER', '')

        if not all([account_sid, auth_token, from_number]):
            return {'success': False, 'error': 'Twilio credentials not configured.'}

        client = Client(account_sid, auth_token)

        # Sanitize message for TwiML
        safe_message = message.replace('&', 'and').replace('<', '').replace('>', '').replace('"', "'")
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice" language="en-IN">
    Hello {employee_name}. This is an automated message from EmpManager Pro.
    {safe_message}
    Thank you. Goodbye.
  </Say>
</Response>"""

        call = client.calls.create(
            twiml=twiml,
            to=to_phone,
            from_=from_number
        )

        return {
            'success': True,
            'call_sid': call.sid,
            'status': call.status,
            'to': to_phone,
        }

    except ImportError:
        return {'success': False, 'error': 'Twilio library not installed.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_call_status(call_sid: str) -> dict:
    """Check the status of a Twilio call."""
    try:
        from twilio.rest import Client
        from flask import current_app
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID') or os.environ.get('TWILIO_ACCOUNT_SID', '')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN') or os.environ.get('TWILIO_AUTH_TOKEN', '')

        client = Client(account_sid, auth_token)
        call = client.calls(call_sid).fetch()

        return {
            'sid': call.sid,
            'status': call.status,
            'duration': call.duration,
            'to': call.to,
            'from': call.from_,
        }
    except Exception as e:
        return {'error': str(e)}


def get_predefined_messages() -> dict:
    """Return predefined voice message templates."""
    return {
        'leave_reminder': 'You have a pending leave request awaiting approval. Please check your EmpManager portal for updates.',
        'payroll_ready': 'Your payslip for this month has been generated and is available on the EmpManager portal.',
        'performance_review': 'Your quarterly performance review has been submitted. Please log in to view your results.',
        'attendance_alert': 'Your attendance has been marked. Please verify it on the EmpManager portal.',
        'welcome': 'Welcome to the team! Your EmpManager account has been created. Please check your email for login credentials.',
    }
