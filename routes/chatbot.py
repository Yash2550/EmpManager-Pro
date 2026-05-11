"""
Chatbot Routes — RAG-powered AI chatbot (Employee only).
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, ChatMessage
from services.ai_services import chat_with_rag
from utils.decorators import role_required

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/ai')


@chatbot_bp.route('/chat')
@login_required
@role_required('employee', 'hr')
def chat_page():
    """Full-page chat interface (employee only)."""
    return render_template('ai/chatbot.html')


@chatbot_bp.route('/chat/send', methods=['POST'])
@login_required
@role_required('employee', 'hr')
def send_message():
    """Send a message and get an AI response."""
    data = request.get_json()
    if not data or not data.get('message', '').strip():
        return jsonify({'error': 'Message is required'}), 400

    user_message = data['message'].strip()

    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    # Get AI response via RAG
    response = chat_with_rag(
        user_message=user_message,
        user_id=current_user.id,
        user_role=current_user.role,
        employee_id=current_user.employee_id
    )

    # Save assistant message
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role='assistant',
        content=response
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        'response': response,
        'message_id': assistant_msg.id,
        'timestamp': assistant_msg.created_at.strftime('%I:%M %p')
    })


@chatbot_bp.route('/chat/history')
@login_required
@role_required('employee', 'hr')
def chat_history():
    """Get chat history for the current user."""
    limit = request.args.get('limit', 50, type=int)
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(
        ChatMessage.created_at.asc()
    ).limit(limit).all()

    return jsonify({
        'messages': [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'timestamp': m.created_at.strftime('%I:%M %p'),
                'date': m.created_at.strftime('%b %d, %Y')
            }
            for m in messages
        ]
    })


@chatbot_bp.route('/chat/clear', methods=['POST'])
@login_required
@role_required('employee', 'hr')
def clear_history():
    """Clear chat history for the current user."""
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Chat history cleared'})
