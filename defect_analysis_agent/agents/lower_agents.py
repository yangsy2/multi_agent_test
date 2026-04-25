"""
하위 Agent 모듈
EQP / Chamber / Layer / MODEL 네 가지 분석 Agent.

각 Agent는 Tool을 호출하여 결과를 받아
이상 유무와 원인을 규칙 기반으로 판단하여 dict로 반환합니다.

이상 기준:
  TREND  : "일정" 이외 → 이상
  MAP    : "특이 MAP 없음" 이외 → 이상
  FDC    : "이상없음" 이외 → 이상
  설비이력: "변경점 없음" 이외 → 이상
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────
# 이상 판별 규칙
# ─────────────────────────────────────────────

NORMAL_VALUES = {
    "TREND":  "일정",
    "MAP":    "특이 MAP 없음",
    "FDC":    "이상없음",
    "설비이력": "변경점 없음",
}


def _is_tool_abnormal(tool_name: str, value: str) -> bool:
    """tool 결과 값이 이상인지 규칙 기반으로 판단합니다."""
    normal = NORMAL_VALUES.get(tool_name)
    if normal is None:
        return False
    return value != normal


def _judge_by_rules(tool_results: list[dict]) -> dict:
    """
    tool 결과 목록을 받아 규칙 기반으로 이상 여부와 원인을 반환합니다.
    """
    abnormal_items = []
    for r in tool_results:
        tool_name = r["tool"]
        value     = r["result"]
        if _is_tool_abnormal(tool_name, value):
            abnormal_items.append(f"{tool_name} {value}")

    if abnormal_items:
        return {
            "is_abnormal": True,
            "reason": " / ".join(abnormal_items),
        }
    return {"is_abnormal": False, "reason": "이상 없음"}


# ─────────────────────────────────────────────
# 하위 Agent 클래스
# ─────────────────────────────────────────────

# Agent별 사용 Tool 정의
AGENT_TOOL_MAP = {
    "EQP":     ["TREND", "FDC"],
    "Chamber": ["TREND", "MAP"],
    "Layer":   ["MAP",   "FDC"],
    "MODEL":   ["TREND", "설비이력"],
}

# 출력용 tool 레이블 (하위 분석 출력 형식에 맞춤)
TOOL_LABEL = {
    "TREND":  "TREND",
    "MAP":    "MAP",
    "FDC":    "FDC",
    "설비이력": "설비이력",
}


class LowerAgent:
    """하위 Agent: 지정된 Tool들을 호출하고 규칙 기반으로 이상 여부를 판단합니다."""

    def __init__(self, name: str):
        self.name      = name
        self.tool_names = AGENT_TOOL_MAP.get(name, [])

    def run(self, lot_id: str, all_tools: dict) -> dict[str, Any]:
        """
        Tool들을 호출하고 판단 결과를 반환합니다.
        반환: {
            "agent": name,
            "lot_id": lot_id,
            "tool_results": [...],
            "is_abnormal": bool,
            "reason": str,
        }
        """
        tool_results = []
        for tname in self.tool_names:
            if tname in all_tools:
                result = all_tools[tname].invoke({"lot_id": lot_id})
                # is_abnormal을 규칙 기반으로 재판단 (tool 자체 판단 무시하고 통일)
                result["is_abnormal"] = _is_tool_abnormal(tname, result["result"])
                tool_results.append(result)

        judgment = _judge_by_rules(tool_results)

        return {
            "agent":        self.name,
            "lot_id":       lot_id,
            "tool_results": tool_results,
            "is_abnormal":  judgment["is_abnormal"],
            "reason":       judgment["reason"],
        }


def make_lower_agents() -> dict[str, LowerAgent]:
    """네 개의 하위 Agent를 생성하여 반환합니다."""
    return {name: LowerAgent(name) for name in AGENT_TOOL_MAP}
