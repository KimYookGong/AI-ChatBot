# Chronos AI - Google Calendar AI Assistant

본 프로젝트는 자연어(채팅) 입력을 분석하여 구글 캘린더의 일정을 추가, 조회, 삭제할 수 있는 **지능형 AI 캘린더 챗봇 프로토타입**입니다.
[Agent.md](Agent.md)에 기술된 **3계층 아키텍처(Directive, Orchestration, Execution)** 사상을 완벽하게 유지하며 설계되었습니다.
사용자의 의도를 분석하는 Layer 2(Gemini)와 실제 구글 캘린더 CRUD를 수행하는 Layer 3(Python & Google APIs)가 투명하게 분리되어 복원력과 견고성을 보장합니다.

---

## 🏗️ 3계층 아키텍처 및 폴더 구조

```text
g:\내 드라이브\2. Antigravity\AI ChatBot/
├── .tmp/                    # 임시 가공 파일 디렉토리
├── directives/              # Layer 1: SOP 및 행동 규정 문서
│   ├── README.md            # SOP 작성 표준 가이드라인
│   ├── sample_directive.md  # 샘플 데이터 SOP 지침서
│   └── chatbot_sop.md       # [NEW] 자연어 파싱 및 인텐트 분류 규칙 지침서
├── execution/                # Layer 3: 결정론적 실행 도구 및 챗봇 엔진
│   ├── static/              # [NEW] 프리미엄 글라스모피즘 챗봇 웹 UI
│   │   ├── index.html       # 챗봇 HTML 구조
│   │   ├── style.css        # 슬릭한 다크 테마 & 형광 액센트 CSS
│   │   └── app.js           # 백엔드 API 비동기 바인딩 JS
│   ├── utils/               
│   │   └── google_auth.py   # Google OAuth 인증 공통 모듈
│   ├── gemini_tool.py       # [NEW] Gemini API 연동 자연어 해석기 (Mock 모드 내장)
│   ├── calendar_tool.py     # [NEW] 구글 캘린더 CRUD 실행 스크립트 (가상 DB 내장)
│   ├── test_chatbot.py      # [NEW] 챗봇 코어 비즈니스 로직 단위 테스트
│   └── chatbot_app.py       # [NEW] FastAPI 백엔드 통합 웹 애플리케이션
├── .env.example             # 환경 변수 템플릿 (GEMINI_API_KEY 가이드 포함)
├── .gitignore               # 임시 폴더 및 민감 정보(credentials, token 등) 차단
├── Agent.md                 # 에이전트 핵심 작동 원리
└── requirements.txt         # FastAPI, Google API Client 등 파이썬 의존성 패키지
```

---

## 🔒 구글 클라우드 콘솔 자격 증명 연동 가이드

챗봇이 실제 사용자의 구글 캘린더와 실시간으로 동기화되어 일정을 추가/조회/삭제하기 위해 아래의 단계를 따라 자격 증명을 셋팅해 주십시오.

### 1단계: Google Cloud 프로젝트 생성 및 API 활성화
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속하여 로그인을 진행합니다.
2. 새 프로젝트를 생성합니다.
3. 상단 검색창에 **Google Calendar API**를 검색하고 해당 API를 **사용(Enable)** 버튼을 눌러 활성화합니다.

### 2단계: OAuth 동의 화면(Consent Screen) 설정
1. 좌측 메뉴에서 **API 및 서비스 > OAuth 동의 화면**으로 이동합니다.
2. User Type을 **외부(External)**로 선택한 후 생성 버튼을 누릅니다.
3. 필수 앱 정보(앱 이름, 사용자 지원 이메일 등)를 작성하고 저장합니다.
4. **테스트 사용자(Test Users)** 탭에서 실제 연동할 본인의 구글 계정 이메일을 추가해야 테스트 연동이 가능합니다. (매우 중요)

### 3단계: OAuth Client ID 발급 및 다운로드
1. 좌측 메뉴의 **사용자 자격 증명(Credentials)** 탭으로 이동합니다.
2. 상단의 **+ 자격 증명 만들기 > OAuth 클라이언트 ID**를 선택합니다.
3. 애플리케이션 유형을 **데스크톱 앱(Desktop App)**으로 선택하고 이름을 기입한 뒤 만들기 버튼을 누릅니다.
4. 생성된 클라이언트 ID의 **JSON 다운로드** 버튼을 클릭하여 파일을 다운로드합니다.
5. 다운로드한 JSON 파일명을 `credentials.json`으로 변경하여 **프로젝트 루트 디렉토리**(`g:\내 드라이브\2. Antigravity\AI ChatBot/`)에 복사해 넣습니다.

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1. 패키지 설치
Python 3.8 이상 가상환경이 셋업된 상태에서 필요한 외부 의존 패키지들을 설치합니다.
```bash
pip install -r requirements.txt
```

### 2. API Key 설정
`.env.example` 파일을 복사하여 `.env` 파일을 만들고, 발급받은 Gemini API Key를 채워 넣습니다.
```env
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
```

### 3. 테스트 코드 실행
캘린더와 의도 파서의 결합 완성도를 검증하기 위해 단위 테스트를 구동합니다.
```bash
python execution/test_chatbot.py
```

### 4. 챗봇 웹 어플리케이션 가동
FastAPI 백엔드 서버를 기동합니다.
```bash
python execution/chatbot_app.py
```
서버가 켜지면 브라우저를 열고 `http://127.0.0.1:8000`에 접속합니다. 슬릭한 프리미엄 글라스모피즘 화면을 통해 자연어로 구글 캘린더 관리를 즐기실 수 있습니다!

> [!TIP]
> **API Key 및 자격 증명서가 없는 상태에서의 작동 (Graceful Fallback)**
> - `GEMINI_API_KEY`나 `credentials.json` 파일이 루트에 배치되지 않은 상태에서 서버를 실행하더라도, 시스템은 에러로 중단되지 않고 **가상 샌드박스 모드(Mock Mode)**로 자동 전환됩니다.
> - 가상 모드에서도 자연어 일정 등록 시나리오, 중간 가공 파일 생성, 카드 뷰어 렌더링 등의 챗봇 핵심 기능을 완전히 체험하실 수 있어, 프로토타입 시연을 안전하게 마칠 수 있습니다.
