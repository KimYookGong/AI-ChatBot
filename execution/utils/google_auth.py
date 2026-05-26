import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# 구글 API 클라이언트 라이브러리 임포트 예외 처리 (방어적 설계)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    HAS_GOOGLE_LIBS = True
except ImportError:
    HAS_GOOGLE_LIBS = False
    print("[Google Auth] Warning: google-api-python-client 등 구글 공식 SDK 라이브러리가 유실되었거나 설치되지 않았습니다.")

def get_google_service(service_name: str, version: str, scopes: list):
    """
    Google API 서비스를 인증받아 생성하는 유틸리티 함수.
    인증 라이브러리가 유실되었을 경우 예외를 일으켜 호출 모듈이 Mock 모드로 자연스럽게 전환되도록 유도합니다.
    """
    if not HAS_GOOGLE_LIBS:
        raise ImportError(
            "[Google Auth] 필수 구글 클라이언트 패키지가 미설치 상태입니다. "
            "'pip install -r requirements.txt'를 실행하여 의존성을 먼저 설정하십시오."
        )

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    token_path = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

    creds = None
    
    # 1. 기존 발급된 token.json 확인
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, scopes)
        except Exception as e:
            print(f"[Google Auth] 기존 토큰 로드 실패: {e}")
            creds = None

    # 2. 유효한 자격 증명이 없거나 만료된 경우 재인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[Google Auth] 만료된 토큰 갱신 중...")
                creds.refresh(Request())
            except Exception as e:
                print(f"[Google Auth] 토큰 갱신 실패: {e}. 다시 인증을 시도합니다.")
                creds = None
                
        if not creds:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"[Google Auth] OAuth 자격 증명 파일 '{credentials_path}'을 찾을 수 없습니다.\n"
                    "Google Cloud Console에서 OAuth 2.0 클라이언트 ID JSON 파일을 다운로드하여 루트 폴더에 배치해 주세요."
                )
            
            print("[Google Auth] 로컬 브라우저를 통한 사용자 OAuth 인증 흐름을 시작합니다...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
            
            # 다음 실행을 위해 자격 증명 저장
            with open(token_path, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
                print(f"[Google Auth] 새로운 액세스 토큰이 {token_path}에 저장되었습니다.")

    # 3. 서비스 빌드 및 반환
    return build(service_name, version, credentials=creds)

if __name__ == "__main__":
    # 간단한 작동 테스트
    TEST_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    print("Google API OAuth 모듈 단독 실행 테스트")
    try:
        service = get_google_service('sheets', 'v4', TEST_SCOPES)
        print("Google Sheets API 서비스 빌드 성공!")
    except FileNotFoundError as fe:
        print(f"경고: {fe}")
    except ImportError as ie:
        print(f"임포트 에러 감지 (정상 Fallback 경로): {ie}")
    except Exception as e:
        print(f"인증 중 오류 발생: {e}")
