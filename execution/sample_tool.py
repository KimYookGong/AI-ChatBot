import os
import json
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="고객 피드백 수집 및 분석을 시뮬레이션하는 결정론적 스크립트")
    parser.add_argument("--source_type", type=str, default="online_store", help="데이터 소스 유형 (예: online_store, mobile_app, social_media)")
    parser.add_argument("--min_rating", type=float, default=3.0, help="필터링할 최소 평점")
    return parser.parse_args()

def generate_mock_feedback():
    """시뮬레이션을 위한 샘플 피드백 데이터 생성"""
    return [
        {"id": 1, "user": "김철수", "rating": 4.5, "comment": "배송이 정말 빠르고 포장 상태도 아주 훌륭합니다! 만족해요.", "source": "online_store"},
        {"id": 2, "user": "이영희", "rating": 2.5, "comment": "디자인은 예쁘지만 마감이 좀 아쉽습니다. 배송도 조금 느렸어요.", "source": "online_store"},
        {"id": 3, "user": "박민수", "rating": 5.0, "comment": "완벽합니다! 제가 찾던 바로 그 상품이네요. 강추합니다.", "source": "online_store"},
        {"id": 4, "user": "최지원", "rating": 3.5, "comment": "사용하기 무난합니다. 가격 대비 성능은 나쁘지 않은 듯.", "source": "mobile_app"},
        {"id": 5, "user": "정다은", "rating": 1.5, "comment": "앱이 너무 자주 튕겨서 결제하기 힘들었습니다. 개선이 필요해요.", "source": "mobile_app"}
    ]

def main():
    args = parse_args()
    print(f"[Execution] 작업을 시작합니다. (Source: {args.source_type}, Min Rating: {args.min_rating})")
    
    # 1. 임시 폴더(.tmp) 경로 설정 및 생성
    # g:\내 드라이브\2. Antigravity\AI ChatBot 기준의 상대/절대 경로 설정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(os.path.dirname(base_dir), '.tmp')
    
    if not os.path.exists(tmp_dir):
        print(f"[Execution] 임시 폴더가 존재하지 않아 새로 생성합니다: {tmp_dir}")
        os.makedirs(tmp_dir, exist_ok=True)
    
    # 2. 데이터 가져오기 및 필터링
    all_data = generate_mock_feedback()
    filtered_data = [
        item for item in all_data 
        if item["source"] == args.source_type and item["rating"] >= args.min_rating
    ]
    
    print(f"[Execution] 원시 데이터 {len(all_data)}건 중 조건에 맞는 데이터 {len(filtered_data)}건 필터링 완료.")

    # 3. 중간 산출물 저장 (JSON 포맷)
    summary_path = os.path.join(tmp_dir, 'feedback_summary.json')
    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        print(f"[Execution] 중간 데이터 저장 완료: {summary_path}")
    except Exception as e:
        print(f"[Error] 중간 데이터 저장 중 오류 발생: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. 최종 보고서 작성 (TXT 포맷)
    report_path = os.path.join(tmp_dir, 'report.txt')
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=========================================\n")
            f.write(f" 고객 피드백 분석 결과 보고서 ({args.source_type})\n")
            f.write("=========================================\n\n")
            f.write(f"■ 분석 기준: 평점 {args.min_rating} 이상\n")
            f.write(f"■ 수집 건수: {len(filtered_data)}건\n\n")
            f.write("■ 피드백 내용 요약:\n")
            if not filtered_data:
                f.write(" - 조건에 맞는 피드백 데이터가 존재하지 않습니다.\n")
            for idx, item in enumerate(filtered_data, 1):
                f.write(f"   {idx}. {item['user']}님 ({item['rating']}점): \"{item['comment']}\"\n")
            f.write("\n=========================================\n")
            f.write("보고서 생성 완료.\n")
        print(f"[Execution] 최종 리포트 파일 저장 완료: {report_path}")
    except Exception as e:
        print(f"[Error] 보고서 파일 저장 중 오류 발생: {e}", file=sys.stderr)
        sys.exit(1)

    print("[Execution] 모든 작업이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    main()
