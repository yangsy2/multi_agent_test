#!/usr/bin/env python3
"""
테스트 스크립트 - Ollama 없이 전체 파이프라인을 검증합니다.
규칙 기반 판단만 사용하므로 LLM이 필요 없습니다.
"""

import sys, os, random

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    current_dir = os.getcwd()

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 재현 가능한 결과를 위해 시드 고정 (필요 시 변경)
random.seed(42)

from graph.pipeline import run_analysis

# ─── 테스트 케이스 ───────────────────────────────
TEST_CASES = [
    ("파티클",   "LOT-A001"),
    ("CD불량",   "LOT-B042"),
    ("두께불량", "LOT-C099"),
]

for defect, lot in TEST_CASES:
    print("\n" + "🔬 " + "=" * 55)
    print(f"  테스트 케이스: DEFECT={defect}, LOT={lot}")
    print("=" * 58)
    report = run_analysis(defect, lot)
    print("\n✅ 분석 완료\n")
