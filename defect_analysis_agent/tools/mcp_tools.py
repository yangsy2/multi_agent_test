"""
MCP Tools - 임시 테스트용 랜덤값 기반 도구 모음
각 Tool은 주어진 리스트에서 랜덤으로 값을 선택하여 반환합니다.
"""

import random
from langchain_core.tools import tool

# ─────────────────────────────────────────────
# 리스트 정의
# ─────────────────────────────────────────────
TREND_LIST = [
    "일정", "상승", "일정", "일정", "일정",
    "산포증가", "일정", "헌팅", "일정", "급증",
    "일정", "일정", "일정", "일정", "일정",
    "일정", "일정", "일정", "일정", "일정",
]

MAP_LIST = [
    "특이 MAP 없음", "특이 MAP 있음", "특이 MAP 없음", "군집 MAP", "특이 MAP 없음",
    "특이 MAP 없음", "특이 MAP 없음", "특이 MAP 없음", "코너 MAP", "특이 MAP 없음",
    "특이 MAP 없음", "특이 MAP 없음", "특이 MAP 없음", "하단 MAP", "특이 MAP 없음",
    "특이 MAP 없음", "특이 MAP 없음", "특이 MAP 없음", "특이 MAP 없음", "특이 MAP 없음",
]

FDC_LIST = [
    "이상없음", "이상없음", "이상있음", "이상없음", "이상없음",
    "이상없음", "이상없음", "이상없음", "이상없음", "이상없음",
    "이상없음", "이상없음", "이상없음", "이상없음", "이상없음",
    "이상있음", "이상없음", "이상없음", "이상없음", "이상없음",
]

# 설비이력 (cTTTM 으로 불림)
HISTORY_LIST = [
    "변경점 없음", "FDC 알람", "변경점 없음", "Error", "변경점 없음",
    "BM", "변경점 없음", "변경점 없음", "변경점 없음", "변경점 없음",
    "변경점 없음", "변경점 없음", "변경점 없음", "변경점 없음", "변경점 없음",
    "변경점 없음", "변경점 없음", "변경점 없음", "변경점 없음", "변경점 없음",
]

# 이상 여부를 판별하기 위한 키워드 세트
ABNORMAL_TREND  = {"상승", "산포증가", "헌팅", "급증"}
ABNORMAL_MAP    = {"특이 MAP 있음", "군집 MAP", "코너 MAP", "하단 MAP"}
ABNORMAL_FDC    = {"이상있음"}
ABNORMAL_HIST   = {"FDC 알람", "Error", "BM"}


# ─────────────────────────────────────────────
# Tool 함수
# ─────────────────────────────────────────────

@tool
def tool_trend(lot_id: str) -> dict:
    """
    TREND 분석 Tool.
    주어진 LOT ID에 대해 TREND 리스트에서 랜덤으로 값을 선택합니다.
    반환값: {"tool": "TREND", "lot_id": ..., "result": ..., "is_abnormal": bool}
    """
    value = random.choice(TREND_LIST)
    return {
        "tool": "TREND",
        "lot_id": lot_id,
        "result": value,
        "is_abnormal": value in ABNORMAL_TREND,
    }


@tool
def tool_map(lot_id: str) -> dict:
    """
    MAP 분석 Tool.
    주어진 LOT ID에 대해 MAP 리스트에서 랜덤으로 값을 선택합니다.
    반환값: {"tool": "MAP", "lot_id": ..., "result": ..., "is_abnormal": bool}
    """
    value = random.choice(MAP_LIST)
    return {
        "tool": "MAP",
        "lot_id": lot_id,
        "result": value,
        "is_abnormal": value in ABNORMAL_MAP,
    }


@tool
def tool_fdc(lot_id: str) -> dict:
    """
    FDC 분석 Tool.
    주어진 LOT ID에 대해 FDC 리스트에서 랜덤으로 값을 선택합니다.
    반환값: {"tool": "FDC", "lot_id": ..., "result": ..., "is_abnormal": bool}
    """
    value = random.choice(FDC_LIST)
    return {
        "tool": "FDC",
        "lot_id": lot_id,
        "result": value,
        "is_abnormal": value in ABNORMAL_FDC,
    }


@tool
def tool_equipment_history(lot_id: str) -> dict:
    """
    설비이력(cTTTM) 분석 Tool.
    주어진 LOT ID에 대해 설비이력 리스트에서 랜덤으로 값을 선택합니다.
    반환값: {"tool": "설비이력", "lot_id": ..., "result": ..., "is_abnormal": bool}
    """
    value = random.choice(HISTORY_LIST)
    return {
        "tool": "설비이력",
        "lot_id": lot_id,
        "result": value,
        "is_abnormal": value in ABNORMAL_HIST,
    }


# 편의를 위한 dict 형태 export
ALL_TOOLS = {
    "TREND": tool_trend,
    "MAP": tool_map,
    "FDC": tool_fdc,
    "설비이력": tool_equipment_history,
}
