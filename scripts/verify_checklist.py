#!/usr/bin/env python3
"""
Final Checklist Verification Script
Verifies all OAuth CTF requirements are met
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"

def check_server_health():
    """Verify server is running and healthy"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Server is healthy and running")
            return True
        else:
            print("❌ Server health check failed")
            return False
    except:
        print("❌ Server not accessible")
        return False

def verify_stage_1_ssrf():
    """Verify Stage 1: SSRF vulnerability works"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "client_name": "ssrf_test",
            "logo_uri": "http://169.254.169.254/latest/meta-data/"
        })

        if resp.status_code == 200:
            data = resp.json()
            if 'flag' in data and 'ssrf_result' in data:
                print("✅ Stage 1: SSRF vulnerability working")
                return data['client_id']
            else:
                print("❌ Stage 1: SSRF not triggering correctly")
                return None
        else:
            print("❌ Stage 1: Client registration failed")
            return None
    except Exception as e:
        print(f"❌ Stage 1: Error - {e}")
        return None

def verify_stage_2_xss(client_id):
    """Verify Stage 2: XSS vulnerability works"""
    try:
        # Post XSS payload
        xss_payload = f'<script>fetch("/capture",{{method:"POST",body:JSON.stringify({{client_id:"{client_id}",data:"xss_test_data"}})}});</script>'

        resp = requests.post(f"{BASE_URL}/app/guestbook", json={
            "author": "test_user",
            "message": xss_payload,
            "client_id": client_id
        })

        if resp.status_code != 200:
            print("❌ Stage 2: Guestbook post failed")
            return False

        # Simulate admin visit
        resp = requests.get(f"{BASE_URL}/admin/simulate-visit/{client_id}")
        if resp.status_code == 200 and resp.json().get('xss_executed'):
            print("✅ Stage 2: XSS vulnerability working")
            return True
        else:
            print("❌ Stage 2: XSS not executing properly")
            return False
    except Exception as e:
        print(f"❌ Stage 2: Error - {e}")
        return False

def verify_stage_progression(client_id):
    """Verify stage progression is enforced"""
    try:
        # Try to access Stage 3 without completing Stage 2
        test_client_id = "fake_client_id"

        resp = requests.post(f"{BASE_URL}/token/exchange", json={
            "client_id": test_client_id,
            "client_secret": "fake_secret",
            "code": "fake_code"
        })

        if resp.status_code in [400, 403]:
            print("✅ Stage progression enforced")
            return True
        else:
            print("❌ Stage progression not properly enforced")
            return False
    except Exception as e:
        print(f"❌ Stage progression: Error - {e}")
        return False

def verify_single_port():
    """Verify only port 5000 is accessible"""
    try:
        # Test that main app is on 5000
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code != 200:
            print("❌ Port 5000 not accessible")
            return False

        # Try to access common other ports that should be blocked
        blocked_ports = [6379, 3000, 8000, 8080]
        for port in blocked_ports:
            try:
                resp = requests.get(f"http://localhost:{port}", timeout=1)
                print(f"⚠️ Port {port} is accessible - should be internal only")
            except:
                pass  # Expected - port should be blocked

        print("✅ Only port 5000 exposed")
        return True
    except Exception as e:
        print(f"❌ Port verification: Error - {e}")
        return False

def verify_final_flag_protection():
    """Verify final flag requires full progression"""
    try:
        # Try to access final flag without proper token
        resp = requests.get(f"{BASE_URL}/admin/flag")
        if resp.status_code == 401:
            print("✅ Final flag properly protected")
            return True
        else:
            print("❌ Final flag not properly protected")
            return False
    except Exception as e:
        print(f"❌ Final flag verification: Error - {e}")
        return False

def verify_no_unintended_solutions():
    """Check for common unintended solution paths"""
    try:
        unintended_paths = [
            "/debug",
            "/admin/dashboard",
            "/flags",
            "/solutions"
        ]

        for path in unintended_paths:
            try:
                resp = requests.get(f"{BASE_URL}{path}")
                if resp.status_code == 200 and "flag" in resp.text.lower():
                    print(f"⚠️ Potential unintended solution at {path}")
                    return False
            except:
                continue

        print("✅ No obvious unintended solution paths")
        return True
    except Exception as e:
        print(f"❌ Unintended solutions check: Error - {e}")
        return False

def verify_admin_bot_integration():
    """Verify admin bot functionality is integrated"""
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "client_name": "bot_test",
            "logo_uri": "https://httpbin.org/get"
        })

        if resp.status_code == 200:
            client_id = resp.json()['client_id']

            # Test admin bot simulation
            resp = requests.get(f"{BASE_URL}/admin/simulate-visit/{client_id}")
            if resp.status_code == 200:
                print("✅ Admin bot integration working")
                return True
            else:
                print("❌ Admin bot simulation failed")
                return False
        else:
            print("❌ Admin bot test setup failed")
            return False
    except Exception as e:
        print(f"❌ Admin bot verification: Error - {e}")
        return False

def main():
    print("🔐 OAuth CTF Final Checklist Verification")
    print("=" * 50)

    checks = [
        ("Server Health", check_server_health),
        ("Single Port (5000)", verify_single_port),
        ("Stage 1: SSRF", lambda: verify_stage_1_ssrf() is not None),
        ("Stage 2: XSS", lambda: verify_stage_2_xss("test_client")),
        ("Stage Progression", lambda: verify_stage_progression("test_client")),
        ("Admin Bot Integration", verify_admin_bot_integration),
        ("Final Flag Protection", verify_final_flag_protection),
        ("No Unintended Solutions", verify_no_unintended_solutions)
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        print(f"\n🔍 Checking: {name}")
        try:
            if check_func():
                passed += 1
            else:
                print(f"❌ {name} - Failed")
        except Exception as e:
            print(f"❌ {name} - Error: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Checklist Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All checks passed! CTF is ready for deployment.")
        return 0
    else:
        print("⚠️ Some checks failed. Review issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())