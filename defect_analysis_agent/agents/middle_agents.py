"""
중간 Agent 모듈
PHT / DRY / CVD / SPT / WET 다섯 개의 공정 Agent.

각 Agent는:
  1. 하위 Agent (EQP / Chamber / Layer / MODEL) 를 순서대로 호출
  2. 모든 하위 결과를 종합하여 해당 공정의 이상 여부와 원인을 LLM 으로 판단
  3. dict 로 결과를 반환
"""

from __future__ import annotations
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from agents.lower_agents import LowerAgent, make_lower_agents


# ─────────────────────────────────────────────
# LLM 팩토리
# ─────────────────────────────────────────────

def _make_llm(model: str = "gemma3:4b"):
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0)
    except Exception as e:
        raise RuntimeError(f"Ollama LLM 초기화 실패: {e}") from e


# ─────────────────────────────────────────────
# 판단 헬퍼
# ─────────────────────────────────────────────

def _judge_process(llm, process_name: str, lower_results: list[dict]) -> dict:
    """하위 Agent 결과를 종합해 공정 이상 여부를 LLM 으로 판단."""
    summary_lines = []
    for r in lower_results:
        status = "이상" if r["is_abnormal"] else "정상"
        summary_lines.append(
            f"  [{r['agent']}] 상태: {status} / 원인: {r['reason']}"
        )
    summary_text = "\n".join(summary_lines)

    system_prompt = (
        f"당신은 반도체 '{process_name}' 공정 전문가입니다. "
        "하위 분석 결과를 종합하여 이 공정이 이상인지 판단하고 "
        "핵심 원인을 한국어로 설명하세요. "
        '응답은 JSON 형식으로만: {"is_abnormal": true/false, "reason": "설명"}'
    )
    user_prompt = (
        f"{process_name} 공정의 하위 분석 결과:\n{summary_text}\n"
        "이 공정의 이상 여부와 원인을 판단해 주세요."
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)
    except Exception:
        # Fallback
        any_ab = any(r["is_abnormal"] for r in lower_results)
        reasons = [r["reason"] for r in lower_results if r["is_abnormal"]]
        return {
            "is_abnormal": any_ab,
            "reason": " / ".join(reasons) if reasons else "이상 없음",
        }


# ─────────────────────────────────────────────
# 중간 Agent 클래스
# ─────────────────────────────────────────────

class MiddleAgent:
    """
    중간 공정 Agent.
    하위 Agent 전체를 순서대로 실행하고 공정 수준 판단을 내립니다.
    """

    def __init__(self, process_name: str, model: str = "gemma3:4b"):
        self.process_name = process_name
        self.llm = _make_llm(model)
        self.lower_agents: dict[str, LowerAgent] = make_lower_agents(model)

    def run(self, lot_id: str, all_tools: dict) -> dict[str, Any]:
        """
        하위 Agent 들을 순서대로 호출하고 공정 판단 결과를 반환합니다.
        반환: {
            "process": process_name,
            "lot_id": lot_id,
            "lower_results": {agent_name: result, ...},
            "is_abnormal": bool,
            "reason": str,
        }
        """
        print(f"\n  ┌─ [{self.process_name}] 공정 분석 시작")

        lower_results = {}
        for agent_name, agent in self.lower_agents.items():
            print(f"  │   → {agent_name} 분석 중...")
            result = agent.run(lot_id, all_tools)
            lower_results[agent_name] = result
            status_icon = "⚠" if result["is_abnormal"] else "✓"
            print(f"  │     {status_icon} {agent_name}: {result['reason']}")

        judgment = _judge_process(self.llm, self.process_name, list(lower_results.values()))

        status = "이상" if judgment["is_abnormal"] else "정상"
        print(f"  └─ [{self.process_name}] 판정: {status} → {judgment['reason']}")

        return {
            "process": self.process_name,
            "lot_id": lot_id,
            "lower_results": lower_results,
            "is_abnormal": judgment.get("is_abnormal", False),
            "reason": judgment.get("reason", ""),
        }


# ─────────────────────────────────────────────
# 중간 Agent 인스턴스 팩토리
# ─────────────────────────────────────────────

PROCESS_NAMES = ["PHT", "DRY", "CVD", "SPT", "WET"]


def make_middle_agents(model: str = "gemma3:4b") -> dict[str, MiddleAgent]:
    """다섯 개의 중간 공정 Agent 를 생성합니다."""
    return {name: MiddleAgent(name, model) for name in PROCESS_NAMES}
