import os
import json
import datetime
from dotenv import load_dotenv

# .env 파일 로드
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(base_dir), '.env'))

# google-generativeai 라이브러리 임포트 예외 처리 (방어적 설계)
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("[Gemini Tool] Warning: google-generativeai 라이브러리가 설치되지 않았습니다. Mock 파서 모드로 자동 전환됩니다.")

# Gemini API 설정
api_key = os.getenv("GEMINI_API_KEY")
if api_key and HAS_GENAI:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"[Gemini Tool] API 설정 오류: {e}. Mock 모드로 강제 우회합니다.")
        api_key = None
else:
    if not api_key:
        print("[Gemini Tool] Info: GEMINI_API_KEY가 존재하지 않아 Mock Parser 모드로 작동합니다.")
    else:
        print("[Gemini Tool] Info: 패키지 부재로 인해 Mock Parser 모드로 작동합니다.")
        api_key = None

def analyze_message_with_gemini(user_message: str) -> dict:
    """
    사용자 자연어 입력을 분석하여 구글 캘린더 작업용 JSON 데이터를 반환합니다.
    API 키가 없거나, 패키지가 미설치 상태이거나, 분석에 실패한 경우
    기본적인 자연어 패턴 분석(Mock Parser)으로 자동 우회하여 극대화된 가용성을 보장합니다.
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    
    # 1. API 키가 있고 패키지가 설치되어 실서버 통신이 가능한 경우
    if api_key and HAS_GENAI:
        try:
            # 구조화된 JSON 출력을 요청하기 위해 시스템 지침 설계
            system_instruction = f"""
You are an expert AI Calendar Assistant. Your task is to analyze user natural language inputs and map them to structured Google Calendar actions.
Always return response in strict JSON format.

Available Actions:
1. "ADD" - To add a new event.
   Arguments: {{ "summary": string, "start_time": "YYYY-MM-DDTHH:MM:SS", "end_time": "YYYY-MM-DDTHH:MM:SS" (default to 1 hour after start_time if not specified), "description": string (optional) }}
2. "LIST" - To view/search events.
   Arguments: {{ "time_min": "YYYY-MM-DDTHH:MM:SS", "time_max": "YYYY-MM-DDTHH:MM:SS" (default to 7 days after time_min if not specified), "query": string (optional) }}
3. "DELETE" - To delete an event.
   Arguments: {{ "query": string (event title or keyword, required), "target_date": "YYYY-MM-DD" (optional) }}
4. "CHAT" - For general conversations, greetings, or off-topic messages.
   Arguments: {{ "response_text": string (your conversational reply) }}

Crucial Instruction on Time Parsing:
- Current system time is: {current_time}
- Relative words like "today", "tomorrow", "this Friday" must be computed relative to this Current system time.
- If morning/afternoon/PM/AM is ambiguous, resolve it logically relative to the nearest future time.
- Return ONLY the raw JSON block without markdown wrappers like ```json.
"""
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=system_instruction
            )
            
            response = model.generate_content(
                user_message,
                generation_config={"response_mime_type": "application/json"}
            )
            
            parsed_result = json.loads(response.text.strip())
            print(f"[Gemini Tool] 분석 성공: {parsed_result}")
            return parsed_result
            
        except Exception as e:
            print(f"[Gemini Tool] Gemini API 실행 또는 파싱 중 오류 발생: {e}. Mock Parser로 복구합니다.")
            
    # 2. Mock Parser 모드 (API 키가 없거나 호출이 실패하거나 패키지가 누락된 경우 작동)
    return parse_message_mock(user_message, current_time)

def parse_message_mock(user_message: str, current_time: str) -> dict:
    """
    결합 제어가 중단되는 것을 방지하는 정교한 룰 기반 Mock 파서.
    """
    msg = user_message.lower().strip()
    now = datetime.datetime.now()
    
    # 2-1. 일정 추가(ADD) 인텐트 분석
    if "등록" in msg or "추가" in msg or "예약" in msg or "잡아" in msg or "회의" in msg or "미팅" in msg:
        summary = "임시 일정"
        for word in ["회의", "미팅", "데이트", "약속", "식사", "세미나"]:
            if word in user_message:
                summary = f"{word} 일정"
                break
                
        # 날짜 추출
        target_date = now.date()
        if "내일" in msg:
            target_date = now.date() + datetime.timedelta(days=1)
        elif "모레" in msg:
            target_date = now.date() + datetime.timedelta(days=2)
            
        # 시간 추출
        hour = 14  # 기본값 오후 2시
        for h in range(1, 25):
            if f"{h}시" in msg:
                hour = h
                if "오후" in msg and h < 12:
                    hour += 12
                break
                
        start_dt = datetime.datetime.combine(target_date, datetime.time(hour, 0))
        end_dt = start_dt + datetime.timedelta(hours=1)
        
        return {
            "action": "ADD",
            "arguments": {
                "summary": summary,
                "start_time": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_time": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "description": f"자연어 분석으로 자동 제안된 일정 (원문: {user_message})"
            }
        }
        
    # 2-2. 일정 조회(LIST) 인텐트 분석
    elif "조회" in msg or "보기" in msg or "일정" in msg or "리스트" in msg:
        return {
            "action": "LIST",
            "arguments": {
                "time_min": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "time_max": (now + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
                "query": ""
            }
        }
        
    # 2-3. 일정 삭제(DELETE) 인텐트 분석
    elif "삭제" in msg or "취소" in msg or "지워" in msg:
        query = "회의"
        for word in ["회의", "미팅", "약속", "식사"]:
            if word in user_message:
                query = word
                break
        return {
            "action": "DELETE",
            "arguments": {
                "query": query
            }
        }
        
    # 2-4. 일반 대화(CHAT) 처리
    else:
        return {
            "action": "CHAT",
            "arguments": {
                "response_text": f"안녕하세요! 반갑습니다. 구글 캘린더 연동 챗봇입니다. 현재 Mock 모드로 응답 중입니다. 입력하신 내용: '{user_message}'"
            }
        }

if __name__ == "__main__":
    test_msg = "내일 오후 3시 디자인 회의 등록해줘"
    print("Mock 분석 결과:", analyze_message_with_gemini(test_msg))
