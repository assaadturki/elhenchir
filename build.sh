#!/bin/bash

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Créer un patch pour flask-login
cat > /opt/render/project/src/.venv/lib/python3.14/site-packages/flask_login/utils.py << 'EOF'
try:
    from werkzeug.urls import url_decode
except ImportError:
    from urllib.parse import unquote
    def url_decode(url, charset='utf-8', errors='replace', decode_keys=False):
        return unquote(url)

# Le reste du fichier original
import hmac
import logging
from hashlib import sha512
from itsdangerous import want_bytes
from flask import request, session, current_app
from werkzeug.security import safe_str_cmp
from werkzeug.local import LocalStack, LocalProxy
from flask_login.config import (COOKIE_NAME, COOKIE_DURATION, COOKIE_SECURE,
                                COOKIE_HTTPONLY, COOKIE_SAMESITE,
                                LOGIN_MESSAGE, LOGIN_MESSAGE_CATEGORY,
                                REFRESH_MESSAGE, REFRESH_MESSAGE_CATEGORY,
                                ID_ATTRIBUTE, AUTH_HEADER_NAME)
from flask_login.signals import user_logged_in, user_logged_out, user_login_confirmed
from flask_login._compat import text_type

def _create_identifier():
    user_agent = request.headers.get('User-Agent')
    if user_agent is not None:
        user_agent = user_agent.encode('utf-8')
    base = f"{request.remote_addr}|{user_agent}"
    if str is bytes:
        base = base.encode('utf-8')
    h = hmac.new(current_app.secret_key.encode('utf-8'), base, sha512)
    return h.hexdigest()

def _get_user():
    if hasattr(request, 'blueprint') and request.blueprint in ('auth', None):
        return current_app.login_manager._load_user()
    return None

def _get_request_blueprint():
    return getattr(request, 'blueprint', None)

def _get_request_blueprint_authorization():
    if hasattr(request, 'blueprint') and request.blueprint in ('auth', None):
        return request.authorization
    return None
EOF

echo "Patch applied successfully"
