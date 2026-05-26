import os
import sys
import unittest

# 상위 경로 임포트 보정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.gemini_tool import analyze_message_with_gemini
from execution.calendar_tool import add_calendar_event, list_calendar_events, delete_calendar_event

class TestChatBotCore(unittest.TestCase):
    
    def test_01_gemini_mock_parser(self):
        """1. API 키가 누락되었을 때 Mock 파서가 자연어 의도를 정확히 파싱하는지 검증합니다."""
        test_msg = "내일 오후 4시 세미나 등록해줘"
        result = analyze_message_with_gemini(test_msg)
        
        self.assertIn("action", result)
        self.assertEqual(result["action"], "ADD")
        self.assertEqual(result["arguments"]["summary"], "세미나 일정")
        self.assertIn("start_time", result["arguments"])
        print("[Test] Mock 파서 가공 성공:", result)

    def test_02_calendar_mock_add_and_list(self):
        """2. 캘린더 도구가 자격증명 누락 상태에서 가상 캘린더(Mock Mode)로 정상 추가 및 조회되는지 검증합니다."""
        # 일정 추가
        add_res = add_calendar_event(
            summary="안티그래비티 테스트 미팅",
            start_time="2026-05-27T14:00:00",
            end_time="2026-05-27T15:00:00",
            description="자동화 단위 테스트"
        )
        
        self.assertTrue(add_res["success"])
        self.assertEqual(add_res["mode"], "mock")
        self.assertEqual(add_res["event"]["summary"], "안티그래비티 테스트 미팅")
        
        # 일정 조회
        list_res = list_calendar_events()
        self.assertTrue(list_res["success"])
        self.assertEqual(list_res["mode"], "mock")
        
        # 우리가 등록한 일정이 포함되었는지 확인
        summaries = [ev["summary"] for ev in list_res["events"]]
        self.assertIn("안티그래비티 테스트 미팅", summaries)
        print("[Test] 가상 캘린더 CRUD 시뮬레이션 성공")

    def test_03_calendar_mock_delete(self):
        """3. 일정 삭제 기능이 Mock 모드에서 정상 작동하는지 검증합니다."""
        # 삭제 수행
        del_res = delete_calendar_event(query="테스트 미팅")
        self.assertTrue(del_res["success"])
        self.assertEqual(del_res["mode"], "mock")
        self.assertEqual(del_res["deleted_event"]["summary"], "안티그래비티 테스트 미팅")
        print("[Test] 가상 캘린더 일정 삭제 시뮬레이션 성공")

if __name__ == "__main__":
    print("====== Chronos AI ChatBot 코어 단위 테스트 구동 ======")
    unittest.main()
