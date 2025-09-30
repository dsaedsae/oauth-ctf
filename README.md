# 🔐 TechCorp Connect - OAuth Security Challenge

> **⚠️ EDUCATIONAL PURPOSE ONLY** - This is an intentionally vulnerable application for security training

A realistic enterprise OAuth platform disguised as "TechCorp Connect" - featuring a 5-stage vulnerability chain for learning OAuth 2.0 security concepts.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Docker-blue.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20TypeScript-blue.svg)

## 📁 프로젝트 구조

```
oauth-ctf/
├── 📂 backend/                # Flask 백엔드 서버
│   ├── app.py                # 메인 OAuth 서버 (모든 취약점 포함)
│   ├── admin_bot.py          # 관리자 봇 시뮬레이션
│   └── requirements.txt      # Python 의존성
├── 📂 frontend/              # Next.js 프론트엔드
│   ├── pages/
│   │   ├── index.tsx        # 🏠 기업용 랜딩 페이지
│   │   ├── developer/
│   │   │   ├── dashboard.tsx # 👨‍💻 Stage 1: OAuth 앱 등록 (SSRF)
│   │   │   └── api-docs.tsx  # 📚 API 문서 (Stage 3-5)
│   │   └── community/
│   │       └── index.tsx     # 💬 Stage 2: 개발자 포럼 (XSS)
│   └── styles/
│       └── globals.css       # 기업용 디자인 시스템
├── 📂 config/                # 인프라 설정
│   ├── docker-compose.new.yml
│   ├── Dockerfile
│   └── nginx.conf
├── 📂 scripts/               # 개발 및 테스트 스크립트
│   ├── Makefile
│   ├── test_solution.py
│   └── verify_checklist.py
├── 📂 docs/                  # 문서
│   └── README.md
├── 📂 templates/             # Flask 템플릿 (레거시)
├── 📂 static/                # 정적 파일 (레거시)
└── docker-compose.yml        # 메인 Docker Compose 설정
```

## 🚀 빠른 시작

### 1. 프로젝트 클론 및 실행
```bash
git clone <repository>
cd oauth-ctf

# Docker Compose로 전체 스택 실행
docker-compose up --build
```

### 2. 접근 URL
- **🏠 메인 사이트**: http://localhost
- **👨‍💻 개발자 대시보드**: http://localhost/developer/dashboard
- **💬 커뮤니티 포럼**: http://localhost/community
- **🔧 백엔드 API**: http://localhost:5000

## 🎯 5단계 공격 체인

### Stage 1: SSRF (Server-Side Request Forgery)
- **진입점**: 개발자 대시보드 > OAuth 앱 등록
- **취약점**: `logo_uri` 파라미터 검증 없음
- **목표**: 내부 메타데이터 서비스 접근

### Stage 2: XSS (Cross-Site Scripting)
- **진입점**: 커뮤니티 포럼 > 게시글 작성
- **취약점**: HTML 콘텐츠 필터링 없음
- **목표**: 관리자 인증 코드 탈취

### Stage 3: PKCE Downgrade & JWT Confusion
- **진입점**: API 문서 > `/token/exchange`
- **취약점**: PKCE 다운그레이드 공격 허용
- **목표**: 탈취한 인증 코드로 토큰 획득

### Stage 4: GraphQL Introspection
- **진입점**: API 문서 > `/graphql`
- **취약점**: 스키마 인트로스펙션 활성화
- **목표**: 숨겨진 ADMIN_SECRETS 스코프 발견

### Stage 5: Refresh Token Scope Escalation
- **진입점**: API 문서 > `/token/refresh`
- **취약점**: 스코프 검증 없음
- **목표**: 관리자 권한 획득

## 🛠️ 개발 스크립트

```bash
# 솔루션 테스트
cd scripts
python test_solution.py

# 체크리스트 검증
python verify_checklist.py

# Make 명령어 (Windows에서는 Git Bash 사용)
make up      # Docker Compose 실행
make down    # 서비스 중지
make logs    # 로그 확인
```

## 🏆 플래그 형식

각 단계 완료 시 다음 형식의 플래그를 획득합니다:
```
TCCTF{vulnerability_description}
```

## 🎨 UI/UX 특징

- **현실적인 기업 브랜딩**: TechCorp Connect
- **전문적인 개발자 도구 인터페이스**
- **자연스러운 사용자 여정으로 취약점 유도**
- **실제 OAuth 서비스와 유사한 UI/UX**

---

**⚠️ 교육 목적 전용**: 이 프로젝트는 보안 교육을 위한 의도적인 취약점을 포함하고 있습니다.