#!/usr/bin/env python3
"""
다중 Agent DEFECT 분석 시스템 - 메인 실행 파일

시작 시 분석 모드를 선택합니다:
  1) DEFECT 분석: DEFECT 명 기준으로 관련 공정을 분석
  2) LOT 분석:    LOT ID 기준으로 전체 공정을 분석
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.pipeline import run_analysis


def select_mode() -> str:
    """분석 모드를 선택합니다."""
    print("\n" + "=" * 58)
    print("🏭  DEFECT 다중 Agent 분석 시스템")
    print("=" * 58)
    print("  분석 모드를 선택하세요:")
    print("  [1] DEFECT 분석")
    print("  [2] LOT 분석")
    print("=" * 58)

    while True:
        choice = input("선택 (1 또는 2): ").strip()
        if choice in ("1", "2"):
            return "defect" if choice == "1" else "lot"
        print("  ⚠ 1 또는 2를 입력하세요.")


def get_defect_name() -> str:
    examples = "파티클, CD불량, 두께불량, PTN_ERR, SCRATCH 등"
    while True:
        name = input(f"  DEFECT 명 입력 ({examples}): ").strip()
        if name:
            return name
        print("  ⚠ DEFECT 명을 입력하세요.")


def get_lot_id() -> str:
    while True:
        lot = input("  LOT ID 입력 (예: LOT-A001): ").strip()
        if lot:
            return lot
        print("  ⚠ LOT ID를 입력하세요.")


def main():
    mode = select_mode()

    if mode == "defect":
        print("\n─── DEFECT 분석 모드 ───────────────────────────────")
        defect_name = get_defect_name()
        lot_id      = get_lot_id()
    else:
        print("\n─── LOT 분석 모드 ──────────────────────────────────")
        lot_id      = get_lot_id()
        defect_name = "전체공정"   # LOT 모드는 전체 공정 분석

    print("\n" + "=" * 58)
    print(f"  분석 시작  DEFECT={defect_name}  LOT={lot_id}")
    print("=" * 58 + "\n")

    report = run_analysis(defect_name, lot_id)
    return report


if __name__ == "__main__":
    main()
