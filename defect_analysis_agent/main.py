#!/usr/bin/env python3
"""
다중 Agent DEFECT 분석 시스템 - 메인 실행 파일

사용법:
  python main.py                          # 기본 테스트 (파티클 / LOT-001)
  python main.py <DEFECT명> <LOT_ID>      # 사용자 지정
  python main.py <DEFECT명> <LOT_ID> <모델명>  # 모델까지 지정
"""

import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.pipeline import run_analysis


def main():
    # 인자 파싱
    defect_name = sys.argv[1] if len(sys.argv) > 1 else "파티클"
    lot_id      = sys.argv[2] if len(sys.argv) > 2 else "LOT-001"
    model       = sys.argv[3] if len(sys.argv) > 3 else "gemma3:4b"

    print("=" * 60)
    print("🏭 DEFECT 다중 Agent 분석 시스템")
    print("=" * 60)
    print(f"  DEFECT  : {defect_name}")
    print(f"  LOT ID  : {lot_id}")
    print(f"  LLM 모델: {model}")
    print("=" * 60)

    report = run_analysis(defect_name, lot_id, model)
    return report


if __name__ == "__main__":
    main()
