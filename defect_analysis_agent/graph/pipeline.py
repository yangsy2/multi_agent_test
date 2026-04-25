"""
LangGraph 파이프라인 정의

그래프 구조:
  START → [lower_analysis] → [middle_analysis] → [upper_analysis] → END
"""

from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

from graph.state import AnalysisState
from tools.mcp_tools import ALL_TOOLS
from agents.middle_agents import make_middle_agents
from agents.upper_agent import UpperAgent


_middle_agents = None
_upper_agent   = None


def _ensure_agents():
    global _middle_agents, _upper_agent
    if _middle_agents is None:
        _middle_agents = make_middle_agents()
    if _upper_agent is None:
        _upper_agent = UpperAgent()


def node_lower_analysis(state: AnalysisState) -> dict:
    """하위 Agent 노드: 모든 공정의 EQP/Chamber/Layer/MODEL 분석 실행"""
    _ensure_agents()
    lot_id = state["lot_id"]

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
    lot_id        = state["lot_id"]
    lower_results = state.get("lower_results", {})

    from agents.middle_agents import _judge_process

    middle_results = {}
    for process_name, mid_agent in _middle_agents.items():
        process_lower = lower_results.get(process_name, {})
        lower_list    = list(process_lower.values())
        judgment      = _judge_process(lower_list)

        middle_results[process_name] = {
            "process":       process_name,
            "lot_id":        lot_id,
            "lower_results": process_lower,
            "is_abnormal":   judgment["is_abnormal"],
            "reason":        judgment["reason"],
        }

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
    print(final_report)

    return {
        "final_report": final_report,
        "messages": [AIMessage(content="최종 이상분석 리포트 생성 완료")],
    }


def build_graph() -> StateGraph:
    builder = StateGraph(AnalysisState)
    builder.add_node("lower_analysis",  node_lower_analysis)
    builder.add_node("middle_analysis", node_middle_analysis)
    builder.add_node("upper_analysis",  node_upper_analysis)
    builder.add_edge(START,            "lower_analysis")
    builder.add_edge("lower_analysis", "middle_analysis")
    builder.add_edge("middle_analysis","upper_analysis")
    builder.add_edge("upper_analysis",  END)
    return builder.compile()


def run_analysis(defect_name: str, lot_id: str) -> str:
    """분석 파이프라인 실행 진입점"""
    graph = build_graph()

    initial_state: AnalysisState = {
        "mode":          "defect",
        "defect_name":   defect_name,
        "lot_id":        lot_id,
        "lower_results": {},
        "middle_results":{},
        "final_report":  "",
        "messages":      [],
    }

    final_state = graph.invoke(initial_state)
    return final_state["final_report"]
