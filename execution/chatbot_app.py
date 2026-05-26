import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from execution.gemini_tool import analyze_message_with_gemini
from execution.calendar_tool import (
    add_calendar_event,
    list_calendar_events,
    delete_calendar_event,
    get_calendar_client
)

app = FastAPI(
    title="Google Calendar AI ChatBot",
    description="자연어 기반의 지능형 구글 캘린더 일정 비서",
    version="1.0.0"
)

# 1. 정적 파일 디렉토리 확보 및 마운트 설정
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

# 2. Pydantic 요청 스키마 정의
class ChatRequest(BaseModel):
    message: str

# 3. API 엔드포인트 정의

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    사용자의 자연어 채팅 입력을 처리하고 행동을 지시합니다.
    """
    user_msg = request.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    print(f"[App Backend] 사용자 입력 수신: '{user_msg}'")
    
    # Step 1: Gemini를 사용해 자연어 의도 분석
    analysis = analyze_message_with_gemini(user_msg)
    action = analysis.get("action", "CHAT")
    args = analysis.get("arguments", {})
    
    reply = ""
    action_result = None

    try:
        # Step 2: 분석된 의도에 맞는 결정론적 캘린더 도구 실행
        if action == "ADD":
            summary = args.get("summary", "새로운 일정")
            start = args.get("start_time")
            end = args.get("end_time")
            desc = args.get("description", "")
            
            if not start:
                raise ValueError("일정 시작 시간이 정의되지 않았습니다.")
                
            res = add_calendar_event(summary, start, end, desc)
            action_result = res
            
            # 응답 메시지 빌드
            event_info = res["event"]
            mode_prefix = "[Mock] " if res["mode"] == "mock" else ""
            reply = f"📅 {mode_prefix}새로운 일정이 캘린더에 성공적으로 등록되었습니다!\n\n**일정명:** {event_info['summary']}\n**시작 시간:** {event_info['start']['dateTime']}\n**설명:** {event_info.get('description', '없음')}"

        elif action == "LIST":
            t_min = args.get("time_min")
            t_max = args.get("time_max")
            query = args.get("query", "")
            
            res = list_calendar_events(t_min, t_max, query)
            action_result = res
            
            events = res.get("events", [])
            mode_prefix = "[Mock] " if res["mode"] == "mock" else ""
            
            if events:
                reply = f"🔍 {mode_prefix}총 {len(events)}개의 일정을 찾았습니다.\n\n"
                for idx, ev in enumerate(events, 1):
                    reply += f"**{idx}. {ev['summary']}**\n- ⏰: {ev['start']['dateTime']}\n- 📝: {ev.get('description', '설명 없음')}\n\n"
            else:
                reply = f"🔍 {mode_prefix}해당 기간 내 등록된 일정이 없습니다."

        elif action == "DELETE":
            query = args.get("query")
            target_date = args.get("target_date")
            
            if not query:
                raise ValueError("삭제하려는 일정 제목이나 키워드가 누락되었습니다.")
                
            res = delete_calendar_event(query, target_date)
            action_result = res
            
            if res.get("success"):
                deleted = res["deleted_event"]
                mode_prefix = "[Mock] " if res["mode"] == "mock" else ""
                reply = f"🗑️ {mode_prefix}아래 일정을 캘린더에서 완전히 취소(삭제)했습니다.\n\n**일정명:** {deleted['summary']}\n**시간:** {deleted['start']['dateTime']}"
            else:
                reply = f"❌ {res.get('message', '일정 취소에 실패했습니다.')}"

        else:  # CHAT
            reply = args.get("response_text", "안녕하세요! 구글 캘린더 비서입니다. 무엇을 도와드릴까요?")

    except Exception as err:
        print(f"[App Backend] 작업 수행 오류 발생: {err}")
        reply = f"⚠️ 일정 작업을 처리하는 동안 내부 에러가 발생했습니다.\n\n**원인:** {str(err)}"

    return {
        "reply": reply,
        "action": action,
        "arguments": args,
        "result": action_result
    }

@app.get("/api/status")
async def status_endpoint():
    """
    현재 구글 API 연동 상태 및 자격 증명 체크 결과를 반환합니다.
    """
    client = get_calendar_client()
    gemini_key_exists = os.getenv("GEMINI_API_KEY") is not None
    
    return {
        "google_calendar_connection": "connected" if client is not None else "mock_mode",
        "gemini_api_connection": "configured" if gemini_key_exists else "mock_mode",
        "env_mode": os.getenv("ENV_MODE", "development")
    }

# 4. 프론트엔드 정적 웹 서빙
# API 라우트 등록 후 마운트해야 static 파일에 가려지지 않음
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    print("[App Backend] FastAPI AI ChatBot 서버 구동 중...")
    uvicorn.run("execution.chatbot_app:app", host="127.0.0.1", port=8000, reload=True)
