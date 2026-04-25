"""
하위 Agent 모듈
EQP / Chamber / Layer / MODEL 네 가지 분석 Agent.

각 Agent는 해당 Tool 을 호출하여 결과를 받아
이상 유무와 원인을 판단하여 dict 로 반환합니다.
"""

from __future__ import annotations
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage


# ─────────────────────────────────────────────
# LLM 팩토리 (Ollama)
# ─────────────────────────────────────────────

def _make_llm(model: str = "gemma3:4b"):
    """Ollama LLM 인스턴스를 반환합니다."""
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0)
    except Exception as e:
        raise RuntimeError(f"Ollama LLM 초기화 실패: {e}") from e


# ─────────────────────────────────────────────
# 공통 판단 헬퍼
# ─────────────────────────────────────────────

def _judge_with_llm(llm, agent_name: str, tool_results: list[dict]) -> dict:
    """
    LLM에게 tool 결과를 넘겨 이상 여부를 판단하게 합니다.
    LLM 호출에 실패하면 규칙 기반으로 fallback 합니다.
    """
    results_text = "\n".join(
        f"  - [{r['tool']}] 결과: {r['result']}  (이상여부: {'이상' if r['is_abnormal'] else '정상'})"
        for r in tool_results
    )

    system_prompt = (
        f"당신은 반도체 공정 분석 전문가입니다. "
        f"'{agent_name}' 분석 단계에서 수집된 데이터를 검토하고, "
        "이상 여부와 주된 원인을 간결하게 한국어로 설명하세요. "
        "응답은 반드시 JSON 형식으로만 출력하세요: "
        '{"is_abnormal": true/false, "reason": "원인 설명"}'
    )
    user_prompt = f"다음은 {agent_name} 단계 분석 데이터입니다:\n{results_text}\n판단해 주세요."

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        raw = response.content.strip()
        # JSON 블록 추출
        if "```" in raw:
            raw = raw.split("```")[1].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)
    except Exception:
        # Fallback: 규칙 기반
        any_abnormal = any(r["is_abnormal"] for r in tool_results)
        reasons = [r["result"] for r in tool_results if r["is_abnormal"]]
        return {
            "is_abnormal": any_abnormal,
            "reason": ", ".join(reasons) if reasons else "이상 없음",
        }


# ─────────────────────────────────────────────
# 하위 Agent 클래스
# ─────────────────────────────────────────────

class LowerAgent:
    """
    하위 Agent 베이스 클래스.
    tool_names : 이 Agent가 사용할 Tool 이름 목록
    """

    def __init__(self, name: str, tool_names: list[str], model: str = "gemma3:4b"):
        self.name = name
        self.tool_names = tool_names
        self.llm = _make_llm(model)

    def run(self, lot_id: str, all_tools: dict) -> dict[str, Any]:
        """
        지정된 tool 들을 호출하고 결과를 판단합니다.
        반환: {"agent": name, "lot_id": lot_id, "tool_results": [...], "is_abnormal": bool, "reason": str}
        """
        tool_results = []
        for tname in self.tool_names:
            if tname in all_tools:
                result = all_tools[tname].invoke({"lot_id": lot_id})
                tool_results.append(result)

        judgment = _judge_with_llm(self.llm, self.name, tool_results)

        return {
            "agent": self.name,
            "lot_id": lot_id,
            "tool_results": tool_results,
            "is_abnormal": judgment.get("is_abnormal", False),
            "reason": judgment.get("reason", ""),
        }


# ─────────────────────────────────────────────
# 구체적인 하위 Agent 인스턴스 팩토리
# ─────────────────────────────────────────────

def make_lower_agents(model: str = "gemma3:4b") -> dict[str, LowerAgent]:
    """네 개의 하위 Agent를 생성하여 반환합니다."""
    return {
        "EQP":     LowerAgent("EQP",     ["TREND", "FDC"],          model),
        "Chamber": LowerAgent("Chamber", ["TREND", "MAP"],           model),
        "Layer":   LowerAgent("Layer",   ["MAP", "FDC"],             model),
        "MODEL":   LowerAgent("MODEL",   ["TREND", "설비이력"],      model),
    }
