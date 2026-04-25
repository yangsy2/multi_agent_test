"""
LangGraph 상태(State) 정의
"""

from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AnalysisState(TypedDict):
    """전체 분석 파이프라인에서 공유되는 상태"""

    # 입력 정보
    defect_name: str          # 분석할 DEFECT 명
    lot_id: str               # 대상 LOT ID

    # 하위 Agent 결과 (공정별)
    lower_results: Annotated[dict[str, Any], lambda a, b: {**a, **b}]

    # 중간 Agent 결과 (공정별 판단)
    middle_results: Annotated[dict[str, Any], lambda a, b: {**a, **b}]

    # 상위 Agent 최종 결과
    final_report: str

    # 메시지 히스토리 (디버깅용)
    messages: Annotated[list, add_messages]
