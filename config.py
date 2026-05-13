import os
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _build_db_url() -> str:
    """
    Resolve the database URL in this priority order:
      1. DATABASE_URL env var (Supabase / Render / Railway)
      2. Individual SUPABASE_* vars (if user prefers that style)
      3. Fallback to local SQLite
    """
    url = os.environ.get('DATABASE_URL', '')

    if url:
        # Support both postgres:// and postgresql:// and ensure driver is specified
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
        elif url.startswith('postgresql://'):
            url = url.replace('postgresql://', 'postgresql+psycopg2://', 1)
            
        # Ensure sslmode=require for PostgreSQL if not already present
        if 'postgresql' in url and 'sslmode=' not in url:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}sslmode=require"
        return url

    # Individual Supabase connection params (alternative)
    host = os.environ.get('SUPABASE_HOST', '')
    if host:
        user = os.environ.get('SUPABASE_USER', 'postgres')
        password = os.environ.get('SUPABASE_PASSWORD', '')
        port = os.environ.get('SUPABASE_PORT', '5432')
        db = os.environ.get('SUPABASE_DB', 'postgres')
        try:
            # Log connection attempt with masked password
            masked_password = '****' if password else ''
            print(f"DEBUG: Connecting to DB at {host}:{port} as {user}")
        except Exception as e:
            print(f"CRITICAL: Database connection failed: {e}")
        return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'

    # Local SQLite fallback
    return 'sqlite:///' + os.path.join(BASE_DIR, 'employee.db')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emp-mgmt-secret-key-2026')
    
    # Session security for Hugging Face iFrames
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = _build_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Extra engine options for Supabase/PostgreSQL (connection pooling + SSL)
    _is_postgres = 'postgresql' in SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,          # drop stale connections automatically
        'pool_recycle': 300,            # recycle connections every 5 min
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 5        # Fail fast (5 seconds) instead of hanging
        } if _is_postgres else {}
    }

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'img', 'avatars')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # ── AI / Groq ──────────────────────────────────
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama3-8b-8192')

    # ── Twilio Voice ──────────────────────────────
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

    # ── ML Models ─────────────────────────────────
    ML_MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')
