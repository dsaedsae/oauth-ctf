#!/usr/bin/env python3
"""
OAuth CTF Challenge - Complete Flask Application
A single Flask app containing all 5 stages of OAuth vulnerabilities.

Stages:
1. SSRF via OAuth Dynamic Client Registration
2. XSS in Guestbook to steal authorization codes
3. PKCE downgrade and JWT confusion attacks
4. GraphQL introspection to discover admin scopes
5. Refresh token scope escalation to admin privileges

Author: OAuth CTF Team
"""

import os
import json
import uuid
import time
import hashlib
import hmac
import base64
import requests
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse

import redis
import jwt
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'oauth_ctf_secret_key_2024_insecure'
CORS(app)

# Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
JWT_SECRET = 'jwt_secret_oauth_ctf_2024'
ADMIN_TOKEN = 'admin_secret_token_12345'

# CTF Flags
FLAGS = {
    'stage1': 'CTF{ssrf_client_registration_exposed}',
    'stage2': 'CTF{xss_authorization_code_stolen}',
    'stage3': 'CTF{pkce_downgrade_jwt_confusion}',
    'stage4': 'CTF{graphql_introspection_admin_scope}',
    'stage5': 'CTF{refresh_token_scope_escalation}',
    'final': 'CTF{oauth_chain_master_2025}'
}

# Initialize Redis connection
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    # Use mock Redis for development
    class MockRedis:
        def __init__(self):
            self.data = {}
            self.lists = {}
            self.expirations = {}

        def set(self, key, value, ex=None):
            self.data[key] = value
            if ex:
                self.expirations[key] = time.time() + ex

        def get(self, key):
            if key in self.expirations and time.time() > self.expirations[key]:
                del self.data[key]
                del self.expirations[key]
                return None
            return self.data.get(key)

        def hset(self, name, key, value):
            if name not in self.data:
                self.data[name] = {}
            self.data[name][key] = value

        def hget(self, name, key):
            return self.data.get(name, {}).get(key)

        def hgetall(self, name):
            return self.data.get(name, {})

        def lpush(self, name, value):
            if name not in self.lists:
                self.lists[name] = []
            self.lists[name].insert(0, value)

        def lrange(self, name, start, end):
            return self.lists.get(name, [])[start:end+1 if end != -1 else None]

        def exists(self, key):
            return key in self.data

        def delete(self, *keys):
            for key in keys:
                self.data.pop(key, None)
                self.expirations.pop(key, None)

    r = MockRedis()

# Helper Functions
def generate_client_id():
    """Generate unique client ID"""
    return f"oauth_client_{uuid.uuid4().hex[:16]}"

def generate_client_secret():
    """Generate client secret"""
    return f"secret_{uuid.uuid4().hex[:16]}"

def generate_auth_code():
    """Generate authorization code"""
    return f"auth_code_{uuid.uuid4().hex}"

def generate_jwt_token(client_id, scope='USER_READ', token_type='access'):
    """Generate JWT token with intentional vulnerabilities"""
    payload = {
        'client_id': client_id,
        'scope': scope,
        'token_type': token_type,  # VULN: Identical structure for ID and access tokens
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600,
        'iss': 'oauth-ctf',
        'aud': 'oauth-ctf-api'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None

def extract_client_id(request):
    """Extract client ID from request"""
    if request.json:
        return request.json.get('client_id')
    elif request.form:
        return request.form.get('client_id')
    elif request.args:
        return request.args.get('client_id')
    elif hasattr(request, 'authorization') and request.authorization:
        return request.authorization.get('username')
    return None

def get_stage_hint(stage_num):
    """Get hint for specific stage"""
    hints = {
        1: "Look for SSRF vulnerability in OAuth client registration - check logo_uri parameter",
        2: "Find XSS in guestbook system - admin bot visits every 30 seconds",
        3: "Try PKCE downgrade attack - exchange S256 code with 'plain' method",
        4: "Enable GraphQL introspection to discover admin schema and endpoints",
        5: "Use refresh token scope escalation to gain admin privileges"
    }
    return hints.get(stage_num, "Complete the previous stages first")

def track_stage_progress(client_id, stage):
    """Track stage completion using Redis key structure"""
    # Store completion timestamp
    stage_key = f"client:{client_id}:stage{stage}"
    r.set(stage_key, int(time.time()))
    print(f"✅ Stage {stage} completed for client {client_id}")

def get_client_progress(client_id):
    """Get completion status for all stages using Redis key structure"""
    progress = {}
    for stage in range(1, 6):
        stage_key = f"client:{client_id}:stage{stage}"
        progress[f'stage{stage}'] = r.get(stage_key) is not None
    return progress

def require_stage(stage_num):
    """Stage verification decorator with Redis key structure"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_id = extract_client_id(request)
            if not client_id:
                return jsonify({"error": "Client ID required"}), 400

            # Check previous stage completion
            for i in range(1, stage_num):
                stage_key = f"client:{client_id}:stage{i}"
                if not r.get(stage_key):
                    return jsonify({
                        "error": f"Complete stage {i} first",
                        "hint": get_stage_hint(i),
                        "current_progress": get_client_progress(client_id)
                    }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

def make_ssrf_request(url):
    """VULN: Perform SSRF request without validation"""
    try:
        print(f"🚨 SSRF: Making request to {url}")

        # VULN: No URL validation - allows access to internal networks
        response = requests.get(url, timeout=5, allow_redirects=True)

        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text[:1000],  # Limit response size
            'url': url
        }
    except Exception as e:
        return {
            'error': str(e),
            'url': url
        }

# HTML Templates
WELCOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OAuth CTF Challenge</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
        .stage { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .completed { background-color: #d4edda; border-color: #c3e6cb; }
        .current { background-color: #fff3cd; border-color: #ffeaa7; }
        .locked { background-color: #f8f9fa; border-color: #dee2e6; color: #6c757d; }
        .flag { background-color: #d1ecf1; padding: 10px; font-family: monospace; margin: 10px 0; }
        .vulnerability { background-color: #f8d7da; padding: 10px; margin: 10px 0; border-radius: 5px; }
        pre { background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }
        button { background-color: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .hint { background-color: #e7f3ff; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <h1>🔐 OAuth CTF Challenge</h1>
    <p>Welcome to the OAuth Security Challenge! Complete all 5 stages to capture the final flag.</p>

    {% if client_id %}
    <div class="stage completed">
        <h3>Your Client ID: <code>{{ client_id }}</code></h3>
        <p>Use this client_id for all subsequent requests.</p>
    </div>
    {% endif %}

    <!-- Stage 1: SSRF -->
    <div class="stage {{ 'completed' if progress.stage1 else 'current' }}">
        <h3>Stage 1: OAuth Dynamic Client Registration (SSRF)</h3>
        <p><strong>Objective:</strong> Exploit SSRF vulnerability in client registration</p>
        <p><strong>Target:</strong> <code>POST /auth/register</code></p>

        {% if progress.stage1 %}
            <div class="flag">🚩 FLAG: {{ flags.stage1 }}</div>
        {% else %}
            <div class="vulnerability">
                <strong>Vulnerability:</strong> The logo_uri parameter is fetched without validation!
            </div>
            <div class="hint">
                <strong>Hint:</strong> Try accessing internal metadata services like http://169.254.169.254/latest/meta-data/
            </div>
            <form onsubmit="registerClient(event)">
                <input type="text" id="client_name" placeholder="Client Name" required><br><br>
                <input type="url" id="logo_uri" placeholder="Logo URI (Try SSRF payload)" required><br><br>
                <button type="submit">Register OAuth Client</button>
            </form>
        {% endif %}
    </div>

    <!-- Stage 2: XSS -->
    <div class="stage {{ 'completed' if progress.stage2 else ('current' if progress.stage1 else 'locked') }}">
        <h3>Stage 2: XSS in Guestbook</h3>
        <p><strong>Objective:</strong> Steal authorization code via XSS</p>
        <p><strong>Target:</strong> <code>/app/guestbook</code></p>

        {% if progress.stage2 %}
            <div class="flag">🚩 FLAG: {{ flags.stage2 }}</div>
        {% elif progress.stage1 %}
            <div class="vulnerability">
                <strong>Vulnerability:</strong> Guestbook renders HTML without escaping!
            </div>
            <div class="hint">
                <strong>Hint:</strong> Look for the hidden auth-code div when admin visits
            </div>
            <a href="/app/guestbook"><button>Go to Guestbook</button></a>
        {% else %}
            <p>🔒 Complete Stage 1 first</p>
        {% endif %}
    </div>

    <!-- Stage 3: PKCE & JWT -->
    <div class="stage {{ 'completed' if progress.stage3 else ('current' if progress.stage2 else 'locked') }}">
        <h3>Stage 3: PKCE Downgrade & JWT Confusion</h3>
        <p><strong>Objective:</strong> Exchange stolen auth code with vulnerabilities</p>
        <p><strong>Target:</strong> <code>POST /token/exchange</code></p>

        {% if progress.stage3 %}
            <div class="flag">🚩 FLAG: {{ flags.stage3 }}</div>
        {% elif progress.stage2 %}
            <div class="vulnerability">
                <strong>Vulnerabilities:</strong><br>
                1. PKCE method downgrade (accepts 'plain')<br>
                2. Identical JWT structure for ID and access tokens
            </div>
            <div class="hint">
                <strong>Hint:</strong> Use code_challenge_method=plain and examine JWT tokens
            </div>
        {% else %}
            <p>🔒 Complete Stage 2 first</p>
        {% endif %}
    </div>

    <!-- Stage 4: GraphQL -->
    <div class="stage {{ 'completed' if progress.stage4 else ('current' if progress.stage3 else 'locked') }}">
        <h3>Stage 4: GraphQL Introspection</h3>
        <p><strong>Objective:</strong> Discover admin scopes via introspection</p>
        <p><strong>Target:</strong> <code>POST /graphql</code></p>

        {% if progress.stage4 %}
            <div class="flag">🚩 FLAG: {{ flags.stage4 }}</div>
        {% elif progress.stage3 %}
            <div class="vulnerability">
                <strong>Vulnerability:</strong> GraphQL introspection enabled in production!
            </div>
            <div class="hint">
                <strong>Hint:</strong> Use __schema query to discover available scopes
            </div>
        {% else %}
            <p>🔒 Complete Stage 3 first</p>
        {% endif %}
    </div>

    <!-- Stage 5: Scope Escalation -->
    <div class="stage {{ 'completed' if progress.stage5 else ('current' if progress.stage4 else 'locked') }}">
        <h3>Stage 5: Refresh Token Scope Escalation</h3>
        <p><strong>Objective:</strong> Escalate to ADMIN_SECRETS scope</p>
        <p><strong>Target:</strong> <code>POST /token/refresh</code></p>

        {% if progress.stage5 %}
            <div class="flag">🚩 FLAG: {{ flags.stage5 }}</div>
            <div class="flag">🏆 FINAL FLAG: {{ flags.final }}</div>
        {% elif progress.stage4 %}
            <div class="vulnerability">
                <strong>Vulnerability:</strong> Refresh endpoint accepts any scope without validation!
            </div>
            <div class="hint">
                <strong>Hint:</strong> Request ADMIN_SECRETS scope with your refresh token
            </div>
        {% else %}
            <p>🔒 Complete Stage 4 first</p>
        {% endif %}
    </div>

    <div style="margin-top: 30px;">
        <h3>🛠️ Debug Endpoints</h3>
        <p><a href="/debug/codes">View Active Auth Codes</a></p>
        {% if client_id %}
        <p><a href="/debug/client/{{ client_id }}">View Your Progress</a></p>
        {% endif %}
    </div>

    <script>
    async function registerClient(event) {
        event.preventDefault();

        const data = {
            client_name: document.getElementById('client_name').value,
            logo_uri: document.getElementById('logo_uri').value
        };

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                alert('Client registered successfully! Refreshing page...');
                window.location.href = '/?client_id=' + result.client_id;
            } else {
                alert('Registration failed: ' + JSON.stringify(result));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }
    </script>
</body>
</html>
"""

GUESTBOOK_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OAuth CTF - Guestbook</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .message { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .vulnerability { background-color: #f8d7da; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .hidden { display: none; }
        textarea { width: 100%; height: 100px; }
        button { background-color: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>📝 Guestbook - Stage 2</h1>
    <p><a href="/">← Back to Challenge</a></p>

    <div class="vulnerability">
        <strong>⚠️ Vulnerability Notice:</strong> This guestbook renders HTML without escaping!<br>
        Admin regularly checks new messages and has access to authorization codes.
    </div>

    <!-- VULN: Hidden div containing admin's authorization code (for XSS theft) -->
    <div id="auth-code" class="hidden">{{ admin_auth_code }}</div>

    <h3>Leave a Message</h3>
    <form onsubmit="postMessage(event)">
        <input type="text" id="author" placeholder="Your name" required><br><br>
        <textarea id="message" placeholder="Your message (HTML allowed!)" required></textarea><br><br>
        <button type="submit">Post Message</button>
    </form>

    <h3>Recent Messages</h3>
    {% for msg in messages %}
    <div class="message">
        <strong>{{ msg.author|safe }}</strong> <small>({{ msg.timestamp }})</small><br>
        <!-- VULN: Rendering user content without escaping -->
        <div>{{ msg.content|safe }}</div>
    </div>
    {% endfor %}

    <script>
    async function postMessage(event) {
        event.preventDefault();

        const data = {
            author: document.getElementById('author').value,
            message: document.getElementById('message').value
        };

        try {
            const response = await fetch('/app/guestbook', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });

            if (response.ok) {
                alert('Message posted! Admin will review it shortly.');
                location.reload();
            } else {
                alert('Failed to post message');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    }

    // Simulate admin checking messages
    setTimeout(() => {
        console.log('Admin is reviewing messages...');
        const authCode = document.getElementById('auth-code').textContent;
        if (authCode) {
            console.log('Admin auth code available:', authCode);
        }
    }, 2000);
    </script>
</body>
</html>
"""

# Routes Implementation

@app.route('/')
def welcome():
    """Welcome page with challenge introduction and progress tracking"""
    client_id = request.args.get('client_id')

    progress = {}
    if client_id:
        progress = get_client_progress(client_id)

    return render_template_string(WELCOME_TEMPLATE,
                                client_id=client_id,
                                progress=progress,
                                flags=FLAGS)

@app.route('/auth/register', methods=['POST'])
def auth_register():
    """Stage 1: OAuth Dynamic Client Registration with SSRF vulnerability"""
    data = request.get_json()

    if not data or 'client_name' not in data or 'logo_uri' not in data:
        return jsonify({'error': 'client_name and logo_uri required'}), 400

    client_id = generate_client_id()
    client_secret = generate_client_secret()

    # Store client data using new Redis key structure
    client_info = {
        'client_id': client_id,
        'client_secret': client_secret,
        'client_name': data['client_name'],
        'logo_uri': data['logo_uri'],
        'redirect_uris': json.dumps(data.get('redirect_uris', [])),
        'created_at': datetime.now().isoformat()
    }

    # Store client info with new key structure
    r.hset(f"client:{client_id}:info", mapping=client_info)

    # VULN: SSRF via logo_uri without validation
    ssrf_result = make_ssrf_request(data['logo_uri'])

    # Check if SSRF was successful (accessing internal networks)
    is_ssrf_success = False
    if 'error' not in ssrf_result:
        url = data['logo_uri'].lower()
        if any(target in url for target in ['169.254.169.254', 'localhost', '127.0.0.1', '10.', '192.168.', 'metadata']):
            is_ssrf_success = True
            # Mark Stage 1 completion using new Redis key structure
            r.set(f"client:{client_id}:stage1", int(time.time()))

    # Trigger admin bot notification
    r.lpush('admin_notifications', json.dumps({
        'type': 'new_client',
        'client_id': client_id,
        'timestamp': datetime.now().isoformat()
    }))

    response_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'client_name': data['client_name'],
        'logo_uri': data['logo_uri'],
        'ssrf_result': ssrf_result
    }

    if is_ssrf_success:
        response_data['flag'] = FLAGS['stage1']
        response_data['message'] = 'SSRF vulnerability exploited!'

    return jsonify(response_data), 201

@app.route('/app/guestbook', methods=['GET'])
def guestbook_view():
    """Stage 2: Display guestbook with XSS vulnerability"""
    # Get recent messages
    message_data = r.lrange('guestbook_messages', 0, 9)  # Last 10 messages
    messages = []

    for msg_json in message_data:
        try:
            messages.append(json.loads(msg_json))
        except:
            continue

    # VULN: Generate admin authorization code for XSS theft
    admin_auth_code = generate_auth_code()
    r.set(f"admin_code:{admin_auth_code}", json.dumps({
        'client_id': 'admin_client',
        'scope': 'ADMIN_READ',
        'created_at': datetime.now().isoformat()
    }), ex=300)  # 5 minutes

    return render_template_string(GUESTBOOK_TEMPLATE,
                                messages=messages,
                                admin_auth_code=admin_auth_code)

@app.route('/app/guestbook', methods=['POST'])
def guestbook_post():
    """Stage 2: Post message to guestbook (XSS vulnerability)"""
    data = request.get_json()

    if not data or 'author' not in data or 'message' not in data:
        return jsonify({'error': 'author and message required'}), 400

    message_data = {
        'author': data['author'],  # VULN: No sanitization
        'content': data['message'],  # VULN: No sanitization
        'timestamp': datetime.now().isoformat(),
        'id': str(uuid.uuid4())
    }

    # Store message without sanitization
    r.lpush('guestbook_messages', json.dumps(message_data))

    # Check for XSS payload and mark stage as completed
    message_content = data['message'].lower()
    if any(xss in message_content for xss in ['<script>', 'onerror=', 'onload=', 'auth-code', 'document.cookie']):
        client_id = data.get('client_id')

        if client_id:
            # Mark Stage 2 completion using new Redis key structure
            r.set(f"client:{client_id}:stage2", int(time.time()))
            print(f"🚨 XSS payload detected for client {client_id}: {data['message']}")

            return jsonify({
                'message': 'Message posted',
                'xss_detected': True,
                'flag': FLAGS['stage2']
            })
        else:
            print(f"🚨 XSS payload detected but no client_id provided: {data['message']}")

            return jsonify({
                'message': 'Message posted',
                'xss_detected': True,
                'note': 'Include client_id to track progress'
            })

    return jsonify({'message': 'Message posted successfully'})

@app.route('/app/callback')
def oauth_callback():
    """OAuth callback endpoint - generates authorization codes"""
    client_id = request.args.get('client_id', 'demo_client')

    # Generate authorization code
    auth_code = generate_auth_code()

    # Store code in Redis with 5 minute expiration
    code_data = {
        'client_id': client_id,
        'scope': 'USER_READ',
        'created_at': datetime.now().isoformat(),
        'code_challenge': request.args.get('code_challenge', ''),
        'code_challenge_method': request.args.get('code_challenge_method', 'S256')
    }

    r.set(f"auth_code:{auth_code}", json.dumps(code_data), ex=300)

    # VULN: Display code in DOM for XSS theft
    return f"""
    <html>
    <head><title>OAuth Callback</title></head>
    <body>
        <h1>Authorization Successful</h1>
        <p>Authorization code: <span id="auth-code">{auth_code}</span></p>
        <p>You may close this window.</p>
        <script>
            // VULN: Authorization code accessible via JavaScript for XSS theft
            console.log('Authorization code:', '{auth_code}');
        </script>
    </body>
    </html>
    """

@app.route('/token/exchange', methods=['POST'])
@require_stage(2)
def token_exchange():
    """Stage 3: Exchange authorization code with PKCE and JWT vulnerabilities"""
    data = request.get_json()

    required_fields = ['client_id', 'client_secret', 'code']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate client using new key structure
    client_data = r.hgetall(f"client:{data['client_id']}:info")
    if not client_data or client_data.get('client_secret') != data['client_secret']:
        return jsonify({'error': 'Invalid client credentials'}), 401

    # Validate authorization code
    code_data = r.get(f"auth_code:{data['code']}")
    if not code_data:
        return jsonify({'error': 'Invalid or expired authorization code'}), 400

    code_info = json.loads(code_data)

    # VULN #1: Accept PKCE downgrade to 'plain' method
    code_challenge_method = data.get('code_challenge_method', code_info.get('code_challenge_method', 'S256'))

    if code_challenge_method == 'plain':
        print("🚨 PKCE downgrade attack detected - accepting 'plain' method!")
        # Mark Stage 3 completion using new Redis key structure
        r.set(f"client:{data['client_id']}:stage3", int(time.time()))

    # VULN #2: Generate identical JWT structure for both ID and access tokens
    scope = code_info.get('scope', 'USER_READ')

    access_token = generate_jwt_token(data['client_id'], scope, 'access')
    id_token = generate_jwt_token(data['client_id'], scope, 'id')  # VULN: Identical to access token
    refresh_token = f"refresh_{uuid.uuid4().hex}"

    # Store refresh token
    r.set(f"refresh_token:{refresh_token}", json.dumps({
        'client_id': data['client_id'],
        'scope': scope,
        'created_at': datetime.now().isoformat()
    }), ex=86400)  # 24 hours

    # Delete used authorization code
    r.delete(f"auth_code:{data['code']}")

    response_data = {
        'access_token': access_token,
        'id_token': id_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': scope
    }

    if code_challenge_method == 'plain':
        response_data['flag'] = FLAGS['stage3']
        response_data['vulnerability'] = 'PKCE downgrade and JWT confusion'

    return jsonify(response_data)

@app.route('/graphql', methods=['POST'])
@require_stage(3)
def graphql_endpoint():
    """Stage 4: GraphQL endpoint with introspection vulnerability"""

    # Require valid Bearer token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Bearer token required'}), 401

    token = auth_header.split(' ')[1]
    token_data = verify_jwt_token(token)

    if not token_data:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json()
    query = data.get('query', '')

    # VULN: Introspection enabled in production
    if '__schema' in query:
        print("🚨 GraphQL introspection query detected!")
        # Mark Stage 4 completion using new Redis key structure
        r.set(f"client:{token_data['client_id']}:stage4", int(time.time()))

        # Return schema including hidden ADMIN_SECRETS scope
        return jsonify({
            'data': {
                '__schema': {
                    'types': [
                        {
                            'name': 'Query',
                            'fields': [
                                {'name': 'user', 'type': {'name': 'User'}},
                                {'name': 'adminSecrets', 'type': {'name': 'AdminSecret'}}
                            ]
                        },
                        {
                            'name': 'AdminSecret',
                            'description': 'Administrative secrets - requires ADMIN_SECRETS scope',
                            'fields': [
                                {'name': 'id', 'type': {'name': 'ID'}},
                                {'name': 'value', 'type': {'name': 'String'}},
                                {'name': 'scope_required', 'type': {'name': 'String'}}
                            ]
                        }
                    ],
                    'directives': [
                        {
                            'name': 'requireScope',
                            'args': [
                                {'name': 'scope', 'type': {'name': 'String'}},
                                {'name': 'admin_scope', 'defaultValue': 'ADMIN_SECRETS'}
                            ]
                        }
                    ]
                }
            },
            'flag': FLAGS['stage4'],
            'message': 'GraphQL introspection vulnerability exploited! Found ADMIN_SECRETS scope.'
        })

    # Regular GraphQL query
    if 'adminSecrets' in query:
        if 'ADMIN_SECRETS' in token_data.get('scope', ''):
            return jsonify({
                'data': {
                    'adminSecrets': [
                        {'id': '1', 'value': 'database_password_123', 'scope_required': 'ADMIN_SECRETS'},
                        {'id': '2', 'value': 'api_key_secret', 'scope_required': 'ADMIN_SECRETS'}
                    ]
                }
            })
        else:
            return jsonify({'error': 'Insufficient scope - ADMIN_SECRETS required'}), 403

    return jsonify({
        'data': {
            'user': {
                'id': token_data['client_id'],
                'scope': token_data.get('scope', 'USER_READ')
            }
        }
    })

@app.route('/token/refresh', methods=['POST'])
@require_stage(4)
def token_refresh():
    """Stage 5: Refresh token with scope escalation vulnerability"""
    data = request.get_json()

    if 'refresh_token' not in data:
        return jsonify({'error': 'refresh_token required'}), 400

    # Validate refresh token
    token_data = r.get(f"refresh_token:{data['refresh_token']}")
    if not token_data:
        return jsonify({'error': 'Invalid refresh token'}), 401

    token_info = json.loads(token_data)

    # VULN: Accept any requested scope without validation
    requested_scope = data.get('scope', token_info['scope'])

    print(f"🚨 Refresh token scope escalation: {token_info['scope']} -> {requested_scope}")

    if 'ADMIN_SECRETS' in requested_scope:
        # Mark Stage 5 completion using new Redis key structure
        r.set(f"client:{token_info['client_id']}:stage5", int(time.time()))

    # Generate new access token with requested scope
    new_access_token = generate_jwt_token(token_info['client_id'], requested_scope, 'access')

    response_data = {
        'access_token': new_access_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': requested_scope
    }

    if 'ADMIN_SECRETS' in requested_scope:
        response_data['flag'] = FLAGS['stage5']
        response_data['message'] = 'Scope escalation successful! You now have admin privileges.'

    return jsonify(response_data)

@app.route('/admin/flag')
def admin_flag():
    """Final flag endpoint - requires ADMIN_SECRETS scope"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Bearer token required'}), 401

    token = auth_header.split(' ')[1]
    token_data = verify_jwt_token(token)

    if not token_data:
        return jsonify({'error': 'Invalid token'}), 401

    if 'ADMIN_SECRETS' not in token_data.get('scope', ''):
        return jsonify({'error': 'ADMIN_SECRETS scope required'}), 403

    return jsonify({
        'flag': FLAGS['final'],
        'message': 'Congratulations! You have completed the OAuth CTF challenge!',
        'all_flags': FLAGS
    })

# Debug endpoints
@app.route('/debug/client/<client_id>')
def debug_client_progress(client_id):
    """Debug: Show client progress"""
    client_data = r.hgetall(f"client:{client_id}")
    progress = get_client_progress(client_id)

    return jsonify({
        'client_id': client_id,
        'client_data': client_data,
        'progress': progress,
        'completed_stages': sum(progress.values())
    })

@app.route('/debug/codes')
def debug_active_codes():
    """Debug: List active authorization codes"""
    # This is a simplified implementation
    # In a real Redis implementation, you'd scan for keys matching the pattern
    return jsonify({
        'message': 'Active authorization codes',
        'note': 'Use /app/callback?client_id=your_client_id to generate codes'
    })

@app.route('/progress/<client_id>')
def check_progress(client_id):
    """Check progress for specific client using new Redis key structure"""
    progress = get_client_progress(client_id)
    client_info = r.hgetall(f"client:{client_id}:info")

    # Get completion timestamps
    stage_times = {}
    for stage in range(1, 6):
        stage_key = f"client:{client_id}:stage{stage}"
        timestamp = r.get(stage_key)
        if timestamp:
            stage_times[f"stage{stage}_completed"] = timestamp

    return jsonify({
        'client_id': client_id,
        'client_name': client_info.get('client_name', 'Unknown'),
        'progress': progress,
        'completed_stages': sum(progress.values()),
        'total_stages': 5,
        'completion_times': stage_times,
        'next_stage_hint': get_stage_hint(sum(progress.values()) + 1) if sum(progress.values()) < 5 else "All stages completed!"
    })

# XSS Capture endpoints for self-contained attack
@app.route('/capture', methods=['POST'])
def capture_data():
    """Endpoint for XSS payloads to send captured data"""
    data = request.get_json()
    if not data:
        data = {
            'data': request.form.get('data', ''),
            'cookies': request.form.get('cookies', ''),
            'url': request.form.get('url', ''),
            'timestamp': datetime.now().isoformat()
        }

    # Try to extract client_id from captured data or URL
    client_id = data.get('client_id')
    if not client_id:
        # Try to extract from referrer or captured data
        referrer = request.headers.get('Referer', '')
        if 'client_id=' in referrer:
            import urllib.parse
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(referrer).query)
            client_id = parsed.get('client_id', [None])[0]

    if not client_id:
        client_id = 'unknown'

    # Store captured data in Redis
    capture_key = f"xss_capture:{client_id}"
    r.set(capture_key, json.dumps(data), ex=3600)  # Expire in 1 hour

    print(f"🚨 XSS data captured for client {client_id}: {data}")

    # Mark Stage 2 completion if this looks like a successful XSS
    if client_id != 'unknown' and (data.get('data') or data.get('cookies')):
        r.set(f"client:{client_id}:stage2", int(time.time()))

    return jsonify({
        'status': 'captured',
        'client_id': client_id,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/check-capture/<client_id>')
def check_capture(client_id):
    """Check captured XSS data for specific client"""
    capture_key = f"xss_capture:{client_id}"
    captured_data = r.get(capture_key)

    if not captured_data:
        return jsonify({
            'status': 'no_data',
            'message': 'No XSS data captured yet',
            'hint': 'Post XSS payload to guestbook and wait 30 seconds for admin bot'
        })

    data = json.loads(captured_data)
    return jsonify({
        'status': 'captured',
        'data': data,
        'flag': FLAGS['stage2'] if data else None,
        'message': 'XSS payload successfully captured admin data!'
    })

@app.route('/debug/xss-result/<client_id>')
def debug_xss_result(client_id):
    """Debug endpoint to check XSS execution results"""
    capture_key = f"xss_capture:{client_id}"
    captured_data = r.get(capture_key)

    # Check if stage 2 is completed
    stage2_key = f"client:{client_id}:stage2"
    stage2_completed = r.get(stage2_key) is not None

    result = {
        'client_id': client_id,
        'stage2_completed': stage2_completed,
        'has_captured_data': captured_data is not None
    }

    if captured_data:
        result['captured_data'] = json.loads(captured_data)
        result['flag'] = FLAGS['stage2']

    return jsonify(result)

@app.route('/admin/simulate-visit/<client_id>')
def simulate_admin_visit(client_id):
    """Simulate admin bot visiting guestbook for specific client"""
    # Generate unique authorization code for this client
    auth_code = generate_auth_code()

    # Store auth code mapping
    r.set(f"auth_code:{auth_code}", json.dumps({
        'client_id': client_id,
        'code_challenge_method': 'S256',
        'scope': 'USER_READ',
        'created_at': datetime.now().isoformat()
    }), ex=300)  # 5 minutes

    # Get guestbook messages
    messages = []
    message_list = r.lrange('guestbook_messages', 0, -1)
    for msg_json in message_list:
        try:
            messages.append(json.loads(msg_json))
        except:
            continue

    # Simulate admin visiting and executing XSS
    admin_data = {
        'admin_token': 'admin_secret_token_12345',
        'auth_code': auth_code,
        'session_id': f'admin_session_{int(time.time())}',
        'cookies': f'admin_session=admin_secret_token_12345; auth_code={auth_code}',
        'timestamp': datetime.now().isoformat(),
        'user_agent': 'AdminBot/1.0'
    }

    # Check for XSS in messages and simulate execution
    xss_executed = False
    for message in messages:
        content = message.get('content', '').lower()
        if any(xss in content for xss in ['<script>', 'onerror=', 'onload=', 'fetch(', 'document.']):
            print(f"🤖 Admin bot executing XSS in message: {message.get('id')}")

            # Simulate XSS capturing admin data
            capture_key = f"xss_capture:{client_id}"
            r.set(capture_key, json.dumps(admin_data), ex=3600)

            # Mark stage 2 complete
            r.set(f"client:{client_id}:stage2", int(time.time()))

            xss_executed = True
            break

    return jsonify({
        'status': 'visited',
        'client_id': client_id,
        'auth_code': auth_code,
        'xss_executed': xss_executed,
        'message': 'Admin bot visited guestbook with admin session',
        'flag': FLAGS['stage2'] if xss_executed else None
    })

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'oauth-ctf',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': r is not None
    })

if __name__ == '__main__':
    print("🚀 OAuth CTF Challenge starting...")
    print("🎯 Access the challenge at: http://localhost:5000")
    print("📋 Stages: SSRF → XSS → PKCE/JWT → GraphQL → Scope Escalation")
    print("🏆 Final goal: Capture CTF{oauth_chain_master_2025}")

    app.run(host='0.0.0.0', port=5000, debug=True)