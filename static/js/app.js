/* ════════════════════════════════════════════════════════════════
   EmpManager Pro — Application JavaScript
   ════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

    // ── Sidebar Toggle (Mobile) ──────────────────────────────
    const sidebar = document.getElementById('sidebar');
    const mobileToggle = document.getElementById('mobileToggle');
    const mainContent = document.getElementById('mainContent');

    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
        // Close sidebar on clicking outside
        mainContent.addEventListener('click', () => {
            if (sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ── Flash Message Auto-dismiss ───────────────────────────
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((msg, i) => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(() => msg.remove(), 300);
        }, 4000 + i * 500);
    });

    // ── Notification Badge ───────────────────────────────────
    async function updateNotificationBadge() {
        try {
            const resp = await fetch('/employee/notifications/count');
            const data = await resp.json();
            const badges = [
                document.getElementById('notifBadge'),
                document.getElementById('topNotifBadge')
            ];
            badges.forEach(badge => {
                if (badge) {
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            });
        } catch (e) { /* silent */ }
    }
    updateNotificationBadge();
    setInterval(updateNotificationBadge, 30000);

    // ── Password Toggle ──────────────────────────────────────
    window.togglePassword = function (inputId) {
        const input = document.getElementById(inputId);
        const icon = input.parentElement.querySelector('.password-toggle i');
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'fas fa-eye';
        }
    };

    // ── Global Search (debounced) ────────────────────────────
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        let searchTimeout;
        globalSearch.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const q = this.value.trim();
                if (q.length >= 2) {
                    // Navigate to employees page with search
                    window.location.href = `/admin/employees?search=${encodeURIComponent(q)}`;
                }
            }, 600);
        });
    }

    // ── Animate Stat Cards on scroll ─────────────────────────
    const statCards = document.querySelectorAll('.stat-card');
    const observerOptions = { threshold: 0.2 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    statCards.forEach(card => observer.observe(card));

    // ── Confirm Delete ───────────────────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // ── Form Validation Highlight ────────────────────────────
    document.querySelectorAll('.employee-form, .auth-form').forEach(form => {
        form.addEventListener('submit', function (e) {
            let valid = true;
            this.querySelectorAll('[required]').forEach(input => {
                if (!input.value.trim()) {
                    input.style.borderColor = '#ef4444';
                    input.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.1)';
                    valid = false;
                    input.addEventListener('input', function () {
                        this.style.borderColor = '';
                        this.style.boxShadow = '';
                    }, { once: true });
                }
            });
            if (!valid) {
                e.preventDefault();
                const firstInvalid = this.querySelector('[required]:invalid, [style*="border-color: rgb(239"]');
                if (firstInvalid) firstInvalid.focus();
            }
        });
    });

    // ── Toast Notifications ──────────────────────────────────
    window.showToast = function (message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `flash-message flash-${type}`;
        toast.style.position = 'fixed';
        toast.style.top = '80px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.maxWidth = '400px';
        toast.style.animation = 'slideDown 0.3s ease';
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };

    // ── Data Table Row Highlighting ──────────────────────────
    document.querySelectorAll('.data-table tbody tr').forEach(row => {
        row.addEventListener('mouseenter', function () {
            this.style.transition = 'all 0.2s ease';
        });
    });

    // ── Smooth Scroll for Anchor Links ───────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ── Counter Animation for Stats ──────────────────────────
    function animateCounter(el, target) {
        let current = 0;
        const increment = target / 40;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                el.textContent = target;
                clearInterval(timer);
            } else {
                el.textContent = Math.ceil(current);
            }
        }, 25);
    }

    document.querySelectorAll('.stat-info h3').forEach(el => {
        const value = parseInt(el.textContent);
        if (!isNaN(value) && value > 0 && value < 10000) {
            el.textContent = '0';
            const counterObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animateCounter(el, value);
                        counterObserver.unobserve(el);
                    }
                });
            });
            counterObserver.observe(el);
        }
    });

});
