#!/usr/bin/env python3
"""
Mock LLM 을 이용한 단독 테스트 스크립트
Ollama 가 없어도 전체 파이프라인 동작을 확인할 수 있습니다.
"""

import sys, os, json, random
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 노트북 환경을 위해 __file__ 대신 현재 작업 디렉토리 사용
# 만약 스크립트 파일(.py)로 실행한다면 os.path.dirname(os.path.abspath(__file__)) 가 작동합니다.
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    current_dir = os.getcwd()

# 프로젝트 루트 경로를 sys.path에 추가
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ─── Mock LLM ────────────────────────────────
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from typing import Any, List, Optional

class MockLLM(BaseChatModel):
    """규칙 기반 Mock LLM – Ollama 없이 동작"""

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager=None,
        **kwargs: Any,
    ) -> ChatResult:
        last = messages[-1].content if messages else ""
        # 15% 확률로 이상 판정
        is_ab = random.random() < 0.15
        reasons_pool = [
            "TREND 상승 감지됨", "FDC 알람 이력 있음", "MAP 불균일 패턴 확인",
            "설비 BM 이력 있음",
        ]

        reason = random.choice(reasons_pool) if is_ab else "이상 없음"
        payload = json.dumps({"is_abnormal": is_ab, "reason": reason}, ensure_ascii=False)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=payload))])

# ─── 패치: 모든 _make_llm 을 MockLLM 으로 교체 ───
import agents.lower_agents  as la
import agents.middle_agents as ma
import agents.upper_agent   as ua

_mock = MockLLM()
la._make_llm = lambda model=None: _mock
ma._make_llm = lambda model=None: _mock
ua._make_llm = lambda model=None: _mock

# ─── 파이프라인 실행 ──────────────────────────
from graph.pipeline import run_analysis

# 테스트 케이스
TEST_CASES = [
    ("파티클",   "LOT-A001"),
    ("CD불량",   "LOT-B042"),
    ("두께불량", "LOT-C099"),
]

for defect, lot in TEST_CASES:
    print("\n" + "🔬 " + "=" * 58)
    print(f"  테스트 케이스: DEFECT={defect}, LOT={lot}")
    print("=" * 60)
    report = run_analysis(defect, lot, model="mock")
    print("\n✅ 분석 완료\n")
