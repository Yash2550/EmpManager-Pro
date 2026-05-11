/* AI Widget JS */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('chatWidgetToggle');
    const panel = document.getElementById('chatWidgetPanel');
    const closeBtn = document.getElementById('chatWidgetClose');
    const sendBtn = document.getElementById('chatWidgetSend');
    const input = document.getElementById('chatWidgetInput');
    const messages = document.getElementById('chatWidgetMessages');

    if (!toggle) return; // widget not on this page

    toggle.addEventListener('click', function () {
      panel.classList.toggle('open');
    });
    if (closeBtn) closeBtn.addEventListener('click', function () {
      panel.classList.remove('open');
    });

    function sendMsg() {
      if (!input) return;
      const text = input.value.trim();
      if (!text) return;
      appendMsg('user', text);
      input.value = '';

      // typing indicator
      const typing = document.createElement('div');
      typing.className = 'chat-msg assistant';
      typing.id = 'widgetTyping';
      typing.innerHTML = '<div class="chat-msg-avatar"><i class="fas fa-robot"></i></div><div class="chat-msg-content"><div class="chat-msg-bubble">...</div></div>';
      messages.appendChild(typing);
      messages.scrollTop = messages.scrollHeight;

      fetch('/ai/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
        .then(r => r.json())
        .then(data => {
          const t = document.getElementById('widgetTyping');
          if (t) t.remove();
          if (data.response) appendMsg('assistant', data.response);
        })
        .catch(() => {
          const t = document.getElementById('widgetTyping');
          if (t) t.remove();
          appendMsg('assistant', 'Sorry, something went wrong.');
        });
    }

    if (sendBtn) sendBtn.addEventListener('click', sendMsg);
    if (input) input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') sendMsg();
    });

    function appendMsg(role, text) {
      const div = document.createElement('div');
      div.className = 'chat-msg ' + role;
      const icon = role === 'assistant' ? 'fa-robot' : 'fa-user';
      const formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
      div.innerHTML = `<div class="chat-msg-avatar"><i class="fas ${icon}"></i></div><div class="chat-msg-content"><div class="chat-msg-bubble">${formatted}</div></div>`;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }
  });
})();
