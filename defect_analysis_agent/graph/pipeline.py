"""
LangGraph 파이프라인 정의

그래프 구조:
  START
    │
    ▼
  [lower_analysis]   ← 모든 공정의 하위 Agent 를 병렬로 실행
    │
    ▼
  [middle_analysis]  ← 각 공정 중간 Agent 가 하위 결과를 종합
    │
    ▼
  [upper_analysis]   ← 이상분석 상위 Agent 가 최종 리포트 생성
    │
    ▼
  END
"""

from __future__ import annotations
import sys
import os

# 프로젝트 루트를 path 에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

from graph.state import AnalysisState
from tools.mcp_tools import ALL_TOOLS
from agents.lower_agents import make_lower_agents
from agents.middle_agents import make_middle_agents
from agents.upper_agent import UpperAgent


# ─────────────────────────────────────────────
# 노드 함수
# ─────────────────────────────────────────────

_lower_agents  = None
_middle_agents = None
_upper_agent   = None
_model         = "gemma3:4b"


def _ensure_agents():
    global _lower_agents, _middle_agents, _upper_agent
    if _lower_agents is None:
        _lower_agents  = make_lower_agents(_model)
    if _middle_agents is None:
        _middle_agents = make_middle_agents(_model)
    if _upper_agent is None:
        _upper_agent   = UpperAgent(_model)


def node_lower_analysis(state: AnalysisState) -> dict:
    """하위 Agent 노드: 모든 공정의 EQP/Chamber/Layer/MODEL 분석 실행"""
    _ensure_agents()
    lot_id = state["lot_id"]

    print(f"\n{'━'*60}")
    print(f"[하위 분석 노드] LOT={lot_id}")

    # 각 공정의 하위 Agent 실행 (공정 × 하위 Agent 조합)
    lower_results = {}
    for process_name, mid_agent in _middle_agents.items():
        process_lower = {}
        for agent_name, lower_agent in mid_agent.lower_agents.items():
            result = lower_agent.run(lot_id, ALL_TOOLS)
            process_lower[agent_name] = result
        lower_results[process_name] = process_lower

    return {
        "lower_results": lower_results,
        "messages": [AIMessage(content=f"하위 분석 완료: {lot_id}")],
    }


def node_middle_analysis(state: AnalysisState) -> dict:
    """중간 Agent 노드: 하위 결과를 받아 공정별 판단"""
    _ensure_agents()
    lot_id       = state["lot_id"]
    lower_results = state.get("lower_results", {})

    print(f"\n{'━'*60}")
    print(f"[중간 분석 노드] LOT={lot_id}")

    middle_results = {}
    for process_name, mid_agent in _middle_agents.items():
        process_lower = lower_results.get(process_name, {})
        if not process_lower:
            # lower 결과가 없으면 직접 실행
            process_lower = {}
            for agent_name, lower_agent in mid_agent.lower_agents.items():
                process_lower[agent_name] = lower_agent.run(lot_id, ALL_TOOLS)

        # 중간 Agent 에 하위 결과 직접 주입하여 판단만 수행
        import json
        from langchain_core.messages import HumanMessage, SystemMessage

        lower_list = list(process_lower.values())
        from agents.middle_agents import _judge_process
        judgment = _judge_process(mid_agent.llm, process_name, lower_list)

        middle_results[process_name] = {
            "process": process_name,
            "lot_id": lot_id,
            "lower_results": process_lower,
            "is_abnormal": judgment.get("is_abnormal", False),
            "reason": judgment.get("reason", ""),
        }
        icon = "⚠ 이상" if middle_results[process_name]["is_abnormal"] else "✓ 정상"
        print(f"  [{process_name}] {icon}: {middle_results[process_name]['reason']}")

    return {
        "middle_results": middle_results,
        "messages": [AIMessage(content=f"중간 분석 완료: {lot_id}")],
    }


def node_upper_analysis(state: AnalysisState) -> dict:
    """상위 Agent 노드: 최종 이상분석 리포트 생성"""
    _ensure_agents()
    defect_name    = state["defect_name"]
    lot_id         = state["lot_id"]
    middle_results = state.get("middle_results", {})

    final_report = _upper_agent.run(defect_name, lot_id, middle_results)

    return {
        "final_report": final_report,
        "messages": [AIMessage(content="최종 이상분석 리포트 생성 완료")],
    }


# ─────────────────────────────────────────────
# 그래프 빌드
# ─────────────────────────────────────────────

def build_graph(model: str = "gemma3:4b") -> StateGraph:
    global _model
    _model = model

    builder = StateGraph(AnalysisState)

    builder.add_node("lower_analysis",  node_lower_analysis)
    builder.add_node("middle_analysis", node_middle_analysis)
    builder.add_node("upper_analysis",  node_upper_analysis)

    builder.add_edge(START,             "lower_analysis")
    builder.add_edge("lower_analysis",  "middle_analysis")
    builder.add_edge("middle_analysis", "upper_analysis")
    builder.add_edge("upper_analysis",  END)

    return builder.compile()


def run_analysis(
    defect_name: str,
    lot_id: str,
    model: str = "gemma3:4b",
) -> str:
    """분석 파이프라인 실행 진입점"""
    graph = build_graph(model)

    initial_state: AnalysisState = {
        "defect_name":    defect_name,
        "lot_id":         lot_id,
        "lower_results":  {},
        "middle_results": {},
        "final_report":   "",
        "messages":       [],
    }

    final_state = graph.invoke(initial_state)
    return final_state["final_report"]
