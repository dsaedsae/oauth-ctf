#!/usr/bin/env python3
"""
OAuth CTF Challenge - Admin Bot Simulator
Simulates realistic admin user behavior for OAuth approvals and XSS vulnerabilities.

This bot runs two parallel loops:
1. OAuth Approval Loop - Processes new client registrations every 30 seconds
2. XSS Trigger Loop - Visits guestbook and "executes" JavaScript every 30 seconds

NOTE: The main app now includes self-contained XSS simulation via /admin/simulate-visit endpoint.
This standalone bot provides additional realism and can run alongside the main app.

Author: OAuth CTF Team
"""

import os
import json
import uuid
import time
import asyncio
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AdminBot')

class AdminBot:
    """Simulates admin user behavior for OAuth CTF challenge"""

    def __init__(self, redis_url: str = 'redis://localhost:6379', base_url: str = 'http://localhost:5000'):
        self.redis_url = redis_url
        self.base_url = base_url
        self.admin_username = 'admin'
        self.admin_token = 'admin_secret_token_12345'

        # Bot configuration
        self.oauth_approval_interval = 30  # seconds
        self.xss_trigger_interval = 30     # seconds

        # Connect to Redis
        self._connect_redis()

        # Track processed items to avoid duplicates
        self.processed_clients = set()
        self.last_guestbook_check = datetime.now()

        # Admin session simulation
        self.admin_session = {
            'user_id': 'admin_001',
            'username': self.admin_username,
            'token': self.admin_token,
            'privileges': ['read', 'write', 'admin', 'oauth_approve'],
            'login_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        logger.info("🤖 Admin Bot initialized")
        logger.info(f"📍 Target application: {self.base_url}")
        logger.info(f"👑 Admin user: {self.admin_username}")
        logger.info(f"⏰ Check intervals: OAuth={self.oauth_approval_interval}s, XSS={self.xss_trigger_interval}s")

    def _connect_redis(self):
        """Initialize Redis connection with fallback"""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.warning(f"❌ Redis connection failed: {e}")
            logger.info("🔄 Using mock Redis for simulation")
            self.redis = self._create_mock_redis()

    def _create_mock_redis(self):
        """Create mock Redis for development/testing"""
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

            def keys(self, pattern):
                if '*' in pattern:
                    prefix = pattern.replace('*', '')
                    return [key for key in self.data.keys() if key.startswith(prefix)]
                return [pattern] if pattern in self.data else []

            def delete(self, *keys):
                for key in keys:
                    self.data.pop(key, None)
                    self.expirations.pop(key, None)

            def exists(self, key):
                return key in self.data

        return MockRedis()

    def generate_auth_code(self, client_id: str = None) -> str:
        """Generate realistic OAuth authorization code"""
        if client_id:
            # Include client reference for realism
            code_base = f"{client_id}_{uuid.uuid4().hex[:8]}"
        else:
            code_base = uuid.uuid4().hex[:12]

        return f"auth_code_{code_base}_{int(time.time())}"

    def simulate_browser_visit(self, url: str, context: str = "general") -> Dict:
        """Simulate admin browser visit to a URL"""
        visit_data = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'user_agent': 'AdminBot/1.0 (OAuth CTF Challenge)',
            'admin_session': self.admin_session['token'],
            'context': context,
            'referrer': self.base_url,
            'ip_address': '192.168.1.100'  # Simulated admin IP
        }

        logger.info(f"🌐 Admin visiting: {url} (context: {context})")

        # Update admin activity
        self.admin_session['last_activity'] = datetime.now().isoformat()

        return visit_data

    def trigger_oauth_flow(self, client_id: str, client_data: Dict) -> Optional[str]:
        """Simulate full OAuth authorization flow for a client"""
        try:
            logger.info(f"🔐 Starting OAuth approval for client: {client_id}")

            # Step 1: Admin reviews client registration
            self.simulate_browser_visit(
                f"{self.base_url}/admin/clients/{client_id}",
                "client_review"
            )

            # Step 2: Admin checks client legitimacy (simulate SSRF trigger)
            logo_uri = client_data.get('logo_uri', '')
            if logo_uri:
                logger.info(f"🖼️ Admin checking client logo: {logo_uri}")
                # This would trigger the SSRF if logo_uri is malicious
                self.simulate_browser_visit(logo_uri, "logo_verification")

            # Step 3: Admin approves OAuth client
            auth_code = self.generate_auth_code(client_id)

            # Store authorization code with admin context
            code_data = {
                'code': auth_code,
                'client_id': client_id,
                'scope': 'USER_READ',
                'approved_by': self.admin_username,
                'approved_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat(),
                'code_challenge': '',
                'code_challenge_method': 'S256'
            }

            # Store in Redis
            self.redis.set(f"auth_code:{auth_code}", json.dumps(code_data), ex=600)

            # Mark client as approved
            self.redis.hset(f"client:{client_id}", "admin_approved", "true")
            self.redis.hset(f"client:{client_id}", "approved_by", self.admin_username)
            self.redis.hset(f"client:{client_id}", "approved_at", datetime.now().isoformat())
            self.redis.hset(f"client:{client_id}", "auth_code", auth_code)

            logger.info(f"✅ OAuth approved for client {client_id}, code: {auth_code}")

            return auth_code

        except Exception as e:
            logger.error(f"❌ OAuth approval failed for client {client_id}: {e}")
            return None

    def check_and_execute_xss(self, message_data: Dict) -> bool:
        """Simulate XSS execution when admin views guestbook"""
        message_content = message_data.get('content', '').lower()
        message_author = message_data.get('author', 'Unknown')
        message_id = message_data.get('id', 'unknown')

        # Detect potential XSS payloads
        xss_patterns = [
            '<script>',
            '<script ',
            'javascript:',
            'onerror=',
            'onload=',
            'onmouseover=',
            'onclick=',
            'document.cookie',
            'localStorage',
            'sessionStorage',
            'auth-code',
            'admin_token'
        ]

        detected_xss = [pattern for pattern in xss_patterns if pattern in message_content]

        if detected_xss:
            logger.warning(f"🚨 XSS DETECTED in message {message_id} by {message_author}")
            logger.warning(f"🔍 Detected patterns: {detected_xss}")

            # Simulate XSS execution
            self._simulate_xss_execution(message_data, detected_xss)
            return True

        return False

    def _simulate_xss_execution(self, message_data: Dict, xss_patterns: List[str]):
        """Simulate what would happen if XSS executed in admin browser"""
        logger.info("💀 Simulating XSS execution in admin browser...")

        # Simulate various XSS attack outcomes
        if 'document.cookie' in str(xss_patterns):
            logger.warning("🍪 XSS would steal admin cookies!")
            stolen_cookies = f"admin_session={self.admin_token}; user_id=admin_001"
            logger.warning(f"📤 Stolen cookies: {stolen_cookies}")

            # Store evidence of cookie theft
            self.redis.set("xss_stolen_cookies", stolen_cookies, ex=3600)

        if 'auth-code' in str(xss_patterns):
            logger.warning("🔑 XSS would steal authorization codes!")
            # Generate a fresh auth code that XSS could steal
            stolen_auth_code = self.generate_auth_code("admin_client")
            logger.warning(f"📤 Stolen auth code: {stolen_auth_code}")

            # Store the stolen code for the CTF challenge
            self.redis.set("xss_stolen_auth_code", stolen_auth_code, ex=1800)

        if 'localStorage' in str(xss_patterns) or 'admin_token' in str(xss_patterns):
            logger.warning("🔐 XSS would steal admin localStorage tokens!")
            stolen_token = self.admin_token
            logger.warning(f"📤 Stolen admin token: {stolen_token}")

            # Store evidence of token theft
            self.redis.set("xss_stolen_admin_token", stolen_token, ex=3600)

        # Mark that admin has been compromised via XSS
        self.redis.set("admin_xss_compromised", json.dumps({
            'compromised_at': datetime.now().isoformat(),
            'compromised_by': message_data.get('author', 'Unknown'),
            'message_id': message_data.get('id', 'unknown'),
            'xss_patterns': xss_patterns,
            'admin_session': self.admin_session['token']
        }), ex=7200)

        logger.error("🔥 ADMIN SESSION COMPROMISED VIA XSS!")

    async def oauth_approval_loop(self):
        """Main loop for processing OAuth client approvals"""
        logger.info("🔄 Starting OAuth approval loop...")

        while True:
            try:
                # Check for new client registrations
                client_keys = self.redis.keys("client:*")

                for client_key in client_keys:
                    client_id = client_key.split(":")[-1]

                    # Skip if already processed
                    if client_id in self.processed_clients:
                        continue

                    # Get client data
                    client_data = self.redis.hgetall(client_key)

                    if not client_data:
                        continue

                    # Check if client needs admin approval
                    if client_data.get('admin_approved') != 'true':
                        logger.info(f"📋 New client registration found: {client_id}")
                        logger.info(f"🏢 Client name: {client_data.get('client_name', 'Unknown')}")
                        logger.info(f"🖼️ Logo URI: {client_data.get('logo_uri', 'None')}")

                        # Trigger OAuth approval flow
                        auth_code = self.trigger_oauth_flow(client_id, client_data)

                        if auth_code:
                            logger.info(f"✅ Client {client_id} approved with code: {auth_code}")

                        # Mark as processed
                        self.processed_clients.add(client_id)

                    # Small delay between client processing
                    await asyncio.sleep(1)

                logger.debug(f"💤 OAuth approval loop sleeping for {self.oauth_approval_interval}s...")
                await asyncio.sleep(self.oauth_approval_interval)

            except Exception as e:
                logger.error(f"❌ Error in OAuth approval loop: {e}")
                await asyncio.sleep(5)  # Short delay on error

    async def xss_trigger_loop(self):
        """Main loop for visiting guestbook and triggering XSS"""
        logger.info("🔄 Starting XSS trigger loop...")

        while True:
            try:
                # Simulate admin visiting guestbook
                self.simulate_browser_visit(f"{self.base_url}/app/guestbook", "guestbook_review")

                # Check for new guestbook messages
                messages = self.redis.lrange('guestbook_messages', 0, -1)

                if messages:
                    logger.info(f"📝 Admin reviewing {len(messages)} guestbook messages...")

                    xss_found = False
                    for message_json in messages:
                        try:
                            message_data = json.loads(message_json)

                            # Check message timestamp to avoid re-processing old messages
                            message_time = datetime.fromisoformat(message_data.get('timestamp', datetime.now().isoformat()))

                            if message_time > self.last_guestbook_check:
                                logger.info(f"👀 Admin viewing message from: {message_data.get('author', 'Unknown')}")

                                # Check for and "execute" XSS
                                if self.check_and_execute_xss(message_data):
                                    xss_found = True

                                    # Award Stage 2 flag for successful XSS
                                    self._award_xss_flag(message_data)

                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"❌ Error processing message: {e}")

                    if not xss_found:
                        logger.info("✅ No XSS payloads detected in recent messages")

                # Update last check time
                self.last_guestbook_check = datetime.now()

                # Set flag that admin visited guestbook (for CTF mechanics)
                self.redis.set("admin_visited_guestbook", json.dumps({
                    'visited_at': datetime.now().isoformat(),
                    'admin_user': self.admin_username,
                    'session_token': self.admin_token
                }), ex=1800)

                # Generate a fresh admin auth code for XSS theft demonstration
                fresh_auth_code = self.generate_auth_code("admin_session")
                self.redis.set("admin_fresh_auth_code", fresh_auth_code, ex=1800)
                logger.debug(f"🔑 Generated fresh admin auth code: {fresh_auth_code}")

                logger.debug(f"💤 XSS trigger loop sleeping for {self.xss_trigger_interval}s...")
                await asyncio.sleep(self.xss_trigger_interval)

            except Exception as e:
                logger.error(f"❌ Error in XSS trigger loop: {e}")
                await asyncio.sleep(5)  # Short delay on error

    def _award_xss_flag(self, message_data: Dict):
        """Award Stage 2 flag when XSS is successfully executed"""
        flag_data = {
            'flag': 'CTF{xss_authorization_code_stolen}',
            'stage': 2,
            'awarded_at': datetime.now().isoformat(),
            'message_author': message_data.get('author', 'Unknown'),
            'message_id': message_data.get('id', 'unknown'),
            'method': 'xss_guestbook_attack'
        }

        self.redis.set("stage2_flag_awarded", json.dumps(flag_data), ex=86400)
        logger.info(f"🏆 STAGE 2 FLAG AWARDED: {flag_data['flag']}")

    async def run(self):
        """Run both admin bot loops concurrently"""
        logger.info("🚀 Starting Admin Bot with concurrent loops...")

        # Create tasks for both loops
        oauth_task = asyncio.create_task(self.oauth_approval_loop())
        xss_task = asyncio.create_task(self.xss_trigger_loop())

        try:
            # Run both loops concurrently
            await asyncio.gather(oauth_task, xss_task)
        except KeyboardInterrupt:
            logger.info("⏹️ Admin Bot stopped by user")
        except Exception as e:
            logger.error(f"💥 Admin Bot crashed: {e}")
        finally:
            # Cleanup
            oauth_task.cancel()
            xss_task.cancel()

    def run_sync(self):
        """Synchronous wrapper for running the bot"""
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            logger.info("⏹️ Admin Bot stopped")

    # Threading-based alternative (if asyncio is not preferred)
    def run_with_threads(self):
        """Run admin bot using threading instead of asyncio"""
        logger.info("🚀 Starting Admin Bot with threading...")

        # Convert async methods to sync for threading
        def oauth_approval_thread():
            while True:
                try:
                    # Similar logic to oauth_approval_loop but synchronous
                    client_keys = self.redis.keys("client:*")

                    for client_key in client_keys:
                        client_id = client_key.split(":")[-1]

                        if client_id in self.processed_clients:
                            continue

                        client_data = self.redis.hgetall(client_key)

                        if client_data and client_data.get('admin_approved') != 'true':
                            logger.info(f"📋 Processing client: {client_id}")
                            auth_code = self.trigger_oauth_flow(client_id, client_data)
                            self.processed_clients.add(client_id)
                            time.sleep(1)

                    time.sleep(self.oauth_approval_interval)

                except Exception as e:
                    logger.error(f"❌ OAuth thread error: {e}")
                    time.sleep(5)

        def xss_trigger_thread():
            while True:
                try:
                    # Similar logic to xss_trigger_loop but synchronous
                    self.simulate_browser_visit(f"{self.base_url}/app/guestbook", "guestbook_review")

                    messages = self.redis.lrange('guestbook_messages', 0, -1)

                    if messages:
                        for message_json in messages:
                            try:
                                message_data = json.loads(message_json)
                                message_time = datetime.fromisoformat(message_data.get('timestamp', datetime.now().isoformat()))

                                if message_time > self.last_guestbook_check:
                                    if self.check_and_execute_xss(message_data):
                                        self._award_xss_flag(message_data)
                            except:
                                continue

                        self.last_guestbook_check = datetime.now()

                    # Set admin visit flag
                    self.redis.set("admin_visited_guestbook", json.dumps({
                        'visited_at': datetime.now().isoformat(),
                        'admin_user': self.admin_username
                    }), ex=1800)

                    time.sleep(self.xss_trigger_interval)

                except Exception as e:
                    logger.error(f"❌ XSS thread error: {e}")
                    time.sleep(5)

        # Start both threads
        oauth_thread = threading.Thread(target=oauth_approval_thread, daemon=True)
        xss_thread = threading.Thread(target=xss_trigger_thread, daemon=True)

        oauth_thread.start()
        xss_thread.start()

        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Admin Bot stopped by user")

def main():
    """Main entry point"""
    # Configuration from environment
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    base_url = os.getenv('BASE_URL', 'http://localhost:5000')
    use_threading = os.getenv('USE_THREADING', 'false').lower() == 'true'

    # Create and start admin bot
    bot = AdminBot(redis_url=redis_url, base_url=base_url)

    logger.info("🎯 OAuth CTF Admin Bot")
    logger.info("=" * 50)
    logger.info(f"📍 Target: {base_url}")
    logger.info(f"🔗 Redis: {redis_url}")
    logger.info(f"⚙️ Mode: {'Threading' if use_threading else 'Asyncio'}")
    logger.info("=" * 50)

    if use_threading:
        bot.run_with_threads()
    else:
        bot.run_sync()

if __name__ == '__main__':
    main()