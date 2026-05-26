import os
import datetime
from execution.utils.google_auth import get_google_service

# Google Calendar API Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# 샌드박스(Mock) 데이터를 저장할 로컬 가상 메모리 데이터베이스
_mock_calendar_db = [
    {
        "id": "mock_event_1",
        "summary": "주간 마케팅 동향 미팅",
        "start": {"dateTime": "2026-05-27T10:00:00+09:00"},
        "end": {"dateTime": "2026-05-27T11:00:00+09:00"},
        "description": "구글 캘린더 연동 챗봇 프로토타입 설계 회의",
        "htmlLink": "https://calendar.google.com/"
    },
    {
        "id": "mock_event_2",
        "summary": "안티그래비티 AI 파트너쉽 식사 약속",
        "start": {"dateTime": "2026-05-28T12:00:00+09:00"},
        "end": {"dateTime": "2026-05-28T13:30:00+09:00"},
        "description": "고객 경험 시뮬레이션 및 점심 식사",
        "htmlLink": "https://calendar.google.com/"
    }
]

def get_calendar_client():
    """
    실제 구글 캘린더 서비스 빌드를 시도합니다.
    인증 파일이 없거나 구글 연동 중 오류 발생 시 None을 리턴하여 Mock 모드로 동작하도록 합니다.
    """
    try:
        service = get_google_service('calendar', 'v3', SCOPES)
        return service
    except Exception as e:
        print(f"[Calendar Tool] Google Calendar API 인증 실패/자격증명 누락: {e}")
        print("[Calendar Tool] 에러 발생으로 인해 가상 메모리 캘린더 데이터베이스(Mock Mode)를 활성화합니다.")
        return None

def add_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> dict:
    """일정을 캘린더에 추가합니다."""
    client = get_calendar_client()
    
    # 시간 포맷 표준화 (타임존 설정)
    if "+" not in start_time and "Z" not in start_time:
        start_time = f"{start_time}+09:00"
    if "+" not in end_time and "Z" not in end_time:
        end_time = f"{end_time}+09:00"
        
    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Seoul',
        }
    }
    
    # 1. 실제 구글 API 호출
    if client:
        try:
            created_event = client.events().insert(calendarId='primary', body=event_body).execute()
            print(f"[Calendar Tool] 구글 캘린더 일정 등록 성공: {created_event.get('htmlLink')}")
            return {
                "success": True,
                "mode": "production",
                "event": created_event
            }
        except Exception as e:
            print(f"[Calendar Tool] API 호출 중 에러 발생: {e}. Mock 모드로 진행합니다.")
            
    # 2. Mock 모드 실행
    mock_id = f"mock_event_{int(datetime.datetime.now().timestamp())}"
    mock_event = {
        "id": mock_id,
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
        "description": f"[MOCK MODE] {description}",
        "htmlLink": "https://calendar.google.com/"
    }
    _mock_calendar_db.append(mock_event)
    return {
        "success": True,
        "mode": "mock",
        "event": mock_event
    }

def list_calendar_events(time_min: str = None, time_max: str = None, query: str = "") -> dict:
    """일정 리스트를 조회합니다."""
    client = get_calendar_client()
    
    # 기본값 설정
    now_dt = datetime.datetime.now()
    if not time_min:
        time_min = now_dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    if not time_max:
        time_max = (now_dt + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S+09:00")
        
    if "+" not in time_min and "Z" not in time_min:
        time_min = f"{time_min}+09:00"
    if "+" not in time_max and "Z" not in time_max:
        time_max = f"{time_max}+09:00"

    # 1. 실제 구글 API 호출
    if client:
        try:
            events_result = client.events().list(
                calendarId='primary', 
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                q=query if query else None
            ).execute()
            events = events_result.get('items', [])
            return {
                "success": True,
                "mode": "production",
                "events": events
            }
        except Exception as e:
            print(f"[Calendar Tool] API 호출 중 에러 발생: {e}. Mock 모드로 조회합니다.")

    # 2. Mock 모드 조회
    filtered = []
    t_min_dt = datetime.datetime.fromisoformat(time_min.replace('Z', '+00:00'))
    t_max_dt = datetime.datetime.fromisoformat(time_max.replace('Z', '+00:00'))
    
    for item in _mock_calendar_db:
        item_dt_str = item["start"]["dateTime"]
        # ISO 포맷 파싱 보정
        item_dt = datetime.datetime.fromisoformat(item_dt_str.replace('Z', '+00:00'))
        
        # 날짜 범위 체크
        if t_min_dt <= item_dt <= t_max_dt:
            # 검색어 필터링
            if not query or query.lower() in item["summary"].lower() or query.lower() in item.get("description", "").lower():
                filtered.append(item)
                
    return {
        "success": True,
        "mode": "mock",
        "events": sorted(filtered, key=lambda x: x["start"]["dateTime"])
    }

def delete_calendar_event(query: str, target_date: str = None) -> dict:
    """일정을 삭제합니다 (제목 기준 검색 후 매칭되는 이벤트 삭제)."""
    client = get_calendar_client()
    
    # 1. 실제 구글 API 호출
    if client:
        try:
            # 먼저 해당 일정을 검색하여 ID 획득
            search_result = client.events().list(calendarId='primary', q=query, singleEvents=True).execute()
            items = search_result.get('items', [])
            
            if items:
                # 조건에 가장 부합하는 첫 번째 일정을 삭제
                target = items[0]
                client.events().delete(calendarId='primary', eventId=target['id']).execute()
                print(f"[Calendar Tool] 구글 캘린더 일정 삭제 완료: {target['summary']}")
                return {
                    "success": True,
                    "mode": "production",
                    "deleted_event": target
                }
            else:
                return {
                    "success": False,
                    "mode": "production",
                    "message": f"'{query}'에 해당하는 일정을 찾을 수 없습니다."
                }
        except Exception as e:
            print(f"[Calendar Tool] API 일정 삭제 중 에러 발생: {e}. Mock 모드로 진행합니다.")

    # 2. Mock 모드 삭제
    global _mock_calendar_db
    matched = None
    for item in _mock_calendar_db:
        if query.lower() in item["summary"].lower():
            if target_date:
                if target_date in item["start"]["dateTime"]:
                    matched = item
                    break
            else:
                matched = item
                break
                
    if matched:
        _mock_calendar_db.remove(matched)
        return {
            "success": True,
            "mode": "mock",
            "deleted_event": matched
        }
    else:
        return {
            "success": False,
            "mode": "mock",
            "message": f"[Mock Mode] '{query}'에 대치하는 가상 일정을 찾지 못했습니다."
        }

if __name__ == "__main__":
    # 등록 및 조회 통합 테스트
    print("캘린더 추가 테스트:")
    res = add_calendar_event("디자인 회의", "2026-05-27T15:00:00", "2026-05-27T16:00:00", "프로토타입 디자인 검토")
    print(res)
    
    print("\n캘린더 조회 테스트:")
    events_res = list_calendar_events()
    print(events_res)
