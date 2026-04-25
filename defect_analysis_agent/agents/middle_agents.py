"""
중간 Agent 모듈
PHT / DRY / CVD / SPT / WET 다섯 개의 공정 Agent.

각 Agent는:
  1. 하위 Agent (EQP / Chamber / Layer / MODEL) 를 순서대로 호출
  2. 하위 결과를 집계하여 공정의 이상 여부와 원인을 판단
  3. dict 로 결과 반환
"""

from __future__ import annotations
from typing import Any

from agents.lower_agents import LowerAgent, make_lower_agents


PROCESS_NAMES = ["PHT", "DRY", "CVD", "SPT", "WET"]


def _judge_process(lower_results: list[dict]) -> dict:
    """하위 Agent 결과를 집계해 공정 이상 여부를 규칙 기반으로 판단."""
    abnormal_items = [r for r in lower_results if r["is_abnormal"]]
    if abnormal_items:
        reasons = " / ".join(r["reason"] for r in abnormal_items)
        return {"is_abnormal": True, "reason": reasons}
    return {"is_abnormal": False, "reason": "이상 없음"}


class MiddleAgent:
    """중간 공정 Agent: 하위 Agent 전체를 실행하고 공정 수준 판단을 내립니다."""

    def __init__(self, process_name: str):
        self.process_name  = process_name
        self.lower_agents: dict[str, LowerAgent] = make_lower_agents()

    def run(self, lot_id: str, all_tools: dict) -> dict[str, Any]:
        """
        하위 Agent들을 순서대로 호출하고 공정 판단 결과를 반환합니다.
        반환: {
            "process":       process_name,
            "lot_id":        lot_id,
            "lower_results": {agent_name: result, ...},
            "is_abnormal":   bool,
            "reason":        str,
        }
        """
        lower_results = {}
        for agent_name, agent in self.lower_agents.items():
            lower_results[agent_name] = agent.run(lot_id, all_tools)

        judgment = _judge_process(list(lower_results.values()))

        return {
            "process":       self.process_name,
            "lot_id":        lot_id,
            "lower_results": lower_results,
            "is_abnormal":   judgment["is_abnormal"],
            "reason":        judgment["reason"],
        }


def make_middle_agents() -> dict[str, MiddleAgent]:
    """다섯 개의 중간 공정 Agent를 생성합니다."""
    return {name: MiddleAgent(name) for name in PROCESS_NAMES}
