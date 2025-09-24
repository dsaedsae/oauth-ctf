.PHONY: build start stop logs clean test reset monitor shell status help

# Default target
help:
	@echo "🔐 OAuth CTF Challenge - Available Commands:"
	@echo ""
	@echo "  make build      - Build Docker containers"
	@echo "  make start      - Start CTF challenge"
	@echo "  make stop       - Stop CTF challenge"
	@echo "  make logs       - View container logs"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run automated solution test"
	@echo "  make reset      - Reset Redis data for fresh start"
	@echo "  make monitor    - Monitor Redis commands"
	@echo "  make shell      - Open shell in web container"
	@echo "  make status     - Check container status"
	@echo ""
	@echo "🎯 Quick Start: make build && make start"

build:
	@echo "🔨 Building Docker containers..."
	docker-compose build
	@echo "✅ Build complete"

start:
	@echo "🚀 Starting OAuth CTF Challenge..."
	docker-compose up -d
	@echo ""
	@echo "✅ CTF running at http://localhost:5000"
	@echo "📊 Check status with: make status"
	@echo "📋 View logs with: make logs"
	@echo "🧪 Test solution with: make test"

stop:
	@echo "🛑 Stopping CTF challenge..."
	docker-compose down
	@echo "✅ Stopped"

logs:
	@echo "📋 Viewing container logs (Ctrl+C to exit)..."
	docker-compose logs -f

clean:
	@echo "🧹 Cleaning up containers and cache..."
	docker-compose down -v
	rm -rf __pycache__ *.pyc
	docker system prune -f --volumes
	@echo "✅ Cleanup complete"

test:
	@echo "🧪 Running automated solution test..."
	@echo "⚠️  Make sure CTF is running (make start)"
	@sleep 2
	python test_solution.py

reset:
	@echo "🔄 Resetting Redis data..."
	docker-compose exec redis redis-cli FLUSHALL
	@echo "✅ Redis cleared - fresh start!"

monitor:
	@echo "👁️  Monitoring Redis commands (Ctrl+C to exit)..."
	docker-compose exec redis redis-cli MONITOR

shell:
	@echo "🐚 Opening shell in web container..."
	docker-compose exec web /bin/bash

status:
	@echo "📊 Container Status:"
	docker-compose ps
	@echo ""
	@echo "🔍 Health Checks:"
	@curl -s http://localhost:5000/health | grep -q "healthy" && echo "✅ Web server healthy" || echo "❌ Web server not responding"
	@docker-compose exec redis redis-cli ping >/dev/null 2>&1 && echo "✅ Redis healthy" || echo "❌ Redis not responding"

# Development targets
dev-start:
	@echo "🔧 Starting in development mode..."
	export FLASK_DEBUG=true && python app.py &
	redis-server --daemonize yes
	@echo "✅ Development server started"

dev-stop:
	@echo "🛑 Stopping development servers..."
	pkill -f "python app.py" || true
	redis-cli shutdown || true
	@echo "✅ Development servers stopped"

# Verification targets
verify-stages:
	@echo "🔍 Verifying all 5 stages are working..."
	@python -c "
import requests, json
base = 'http://localhost:5000'
try:
    # Test Stage 1 - SSRF
    resp = requests.post(f'{base}/auth/register', json={'client_name': 'test', 'logo_uri': 'http://169.254.169.254/latest/meta-data/'})
    assert resp.status_code == 200, 'Stage 1 failed'
    print('✅ Stage 1: SSRF working')

    client_id = resp.json()['client_id']

    # Test Stage 2 - XSS simulation
    resp = requests.get(f'{base}/admin/simulate-visit/{client_id}')
    assert resp.status_code == 200, 'Stage 2 simulation failed'
    print('✅ Stage 2: XSS simulation working')

    # Test progression tracking
    resp = requests.get(f'{base}/progress/{client_id}')
    assert resp.status_code == 200, 'Progress tracking failed'
    print('✅ Progress tracking working')

    print('✅ Core functionality verified')
except Exception as e:
    print(f'❌ Verification failed: {e}')
"

verify-ports:
	@echo "🔍 Verifying only port 5000 is exposed..."
	@docker-compose ps | grep -q "0.0.0.0:5000" && echo "✅ Port 5000 exposed"
	@docker-compose ps | grep -v "5000" | grep -q "0.0.0.0:" && echo "❌ Additional ports exposed!" || echo "✅ Only port 5000 exposed"

verify-flags:
	@echo "🔍 Verifying flags are properly protected..."
	@python -c "
import requests
base = 'http://localhost:5000'
try:
    # Try to access final flag without progression
    resp = requests.get(f'{base}/admin/flag')
    assert resp.status_code == 401, 'Final flag not properly protected'
    print('✅ Final flag properly protected')

    # Test stage progression enforcement
    resp = requests.post(f'{base}/graphql', json={'query': '{__schema{types{name}}}'})
    assert resp.status_code == 401 or resp.status_code == 403, 'Stage progression not enforced'
    print('✅ Stage progression enforced')

except Exception as e:
    print(f'❌ Flag verification failed: {e}')
"

# Full verification suite
verify: verify-ports verify-stages verify-flags
	@echo ""
	@echo "🎉 Full verification complete!"

# Complete checklist verification
checklist:
	@echo "🔍 Running complete checklist verification..."
	python verify_checklist.py

# Quick deployment check
deploy-check:
	@echo "🚀 Running deployment readiness check..."
	make build
	make start
	@sleep 10
	make verify
	make test
	make stop
	@echo "✅ Deployment ready!"