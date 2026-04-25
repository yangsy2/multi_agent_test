"""
상위 Agent 모듈: 이상분석 Agent

역할:
  - DEFECT 명 기준으로 관련 공정을 식별
  - 중간 Agent 판단 결과를 수집
  - 문서 출력 예시 형식에 맞춰 최종 리포트 생성
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────
# DEFECT → 관련 공정 매핑
# ─────────────────────────────────────────────

DEFECT_PROCESS_MAP: dict[str, list[str]] = {
    "PTN_ERR":   ["PHT", "DRY"],
    "BLACK_SPOT": ["CVD", "SPT", "WET"],
    "CORROSION": ["DRY", "WET"],
    "PTN_OPEN":  ["PHT"],
    "SCRATCH":   ["WET", "SPT"],
    "HABU_YUHAK": ["PHT", "SPT"],
    "FRECKLE":   ["ELA", "WET", "PHT"],
    "파티클":    ["PHT", "DRY", "CVD"],
    "CD불량":    ["PHT", "DRY", "SPT"],
    "두께불량":  ["CVD", "WET"],
    "결함":      ["PHT", "CVD", "WET"],
    "스크래치":  ["WET", "SPT"],
    "오염":      ["PHT", "DRY", "WET"],
    "default":   ["PHT", "DRY", "CVD", "SPT", "WET"],
}

SEP_THICK = "━" * 58
SEP_EQUAL = "=" * 58
SEP_DASH  = "─" * 58


def _get_related_processes(defect_name: str) -> list[str]:
    """DEFECT 명으로 관련 공정 목록을 반환합니다."""
    for key, processes in DEFECT_PROCESS_MAP.items():
        if key in defect_name:
            return processes
    return DEFECT_PROCESS_MAP["default"]


def _format_tool_inline(tool_results: list[dict]) -> str:
    """tool 결과를 '[TREND:일정 | FDC:이상없음]' 형식으로 포매팅합니다."""
    parts = []
    for t in tool_results:
        parts.append(f"{t['tool']}:{t['result']}")
    return "[" + " | ".join(parts) + "]"


def _build_lower_section(relevant: dict[str, dict]) -> list[str]:
    """[하위 분석] 섹션 문자열 목록을 생성합니다."""
    lines = ["[하위 분석]"]
    for process_name, mid_result in relevant.items():
        lower_results = mid_result.get("lower_results", {})
        for agent_name, lr in lower_results.items():
            icon       = "⚠" if lr["is_abnormal"] else "✓"
            tool_str   = _format_tool_inline(lr.get("tool_results", []))
            reason     = lr["reason"]
            lines.append(f"  {process_name}/{agent_name} {icon} {tool_str} → {reason}")
        lines.append("")  # 공정 사이 빈 줄
    return lines


def _build_middle_section(relevant: dict[str, dict]) -> list[str]:
    """[중간 분석] 섹션 문자열 목록을 생성합니다."""
    lines = [SEP_THICK, "[중간 분석]"]
    for process_name, mid_result in relevant.items():
        icon = "⚠" if mid_result["is_abnormal"] else "✓"
        if mid_result["is_abnormal"]:
            # 이상이 있는 경우: 하위 항목별 원인 상세 기술
            lower_issues = []
            for agent_name, lr in mid_result.get("lower_results", {}).items():
                if lr["is_abnormal"]:
                    lower_issues.append(f"{agent_name} 에서 {lr['reason']}")
                else:
                    lower_issues.append(f"{agent_name} 는 이상없음")
            detail = ", ".join(lower_issues)
            lines.append(f"  [{process_name}] {icon} 이상 : {detail}")
        else:
            lines.append(f"  [{process_name}] {icon} 이상 없음")
    lines.append(SEP_THICK)
    return lines


def _build_final_section(defect_name: str, relevant: dict[str, dict]) -> list[str]:
    """[최종 분석] 섹션 문자열 목록을 생성합니다."""
    lines = ["[최종 분석]"]

    abnormal_processes = {p: v for p, v in relevant.items() if v["is_abnormal"]}

    if not abnormal_processes:
        lines.append("전 공정 이상없음. 추가 분석하시겠습니까?")
    else:
        # 이상 공정별 원인 공정 → 중간 원인 → 하위 원인 순으로 정리
        for process_name, mid_result in abnormal_processes.items():
            abnormal_lower = {
                agent: lr
                for agent, lr in mid_result.get("lower_results", {}).items()
                if lr["is_abnormal"]
            }
            if abnormal_lower:
                # 예: "PHT : Chamber 기인 하단 MAP으로 EQP/MODEL 에서 TREND 상승"
                cause_parts = []
                for agent_name, lr in abnormal_lower.items():
                    cause_parts.append(f"{agent_name} ({lr['reason']})")
                causes_str = ", ".join(cause_parts)
                lines.append(f"DEFECT={defect_name} 경우 [{process_name}] 공정 이상 → {causes_str}")

        # MODEL 상관성 언급이 필요한 경우
        model_abnormal_procs = [
            p for p, v in abnormal_processes.items()
            if v.get("lower_results", {}).get("MODEL", {}).get("is_abnormal")
        ]
        if model_abnormal_procs:
            proc_list = ", ".join(model_abnormal_procs)
            lines.append(f"{proc_list} MODEL TREND 이상 확인되므로 MODEL 상관성 확인 필요합니다.")

    lines.append(SEP_THICK)
    return lines


class UpperAgent:
    """이상분석 상위 Agent: 중간 Agent 결과를 종합하여 최종 리포트를 생성합니다."""

    def run(
        self,
        defect_name: str,
        lot_id: str,
        middle_results: dict[str, dict],
    ) -> str:
        """중간 Agent 결과를 종합하여 최종 리포트 문자열을 반환합니다."""
        related   = _get_related_processes(defect_name)
        relevant  = {p: v for p, v in middle_results.items() if p in related}

        output_lines = [
            SEP_EQUAL,
            f"  분석 케이스: DEFECT={defect_name}  LOT={lot_id}",
            SEP_EQUAL,
            "",
        ]

        # 하위 분석
        output_lines.extend(_build_lower_section(relevant))

        # 중간 분석
        output_lines.extend(_build_middle_section(relevant))
        output_lines.append("")

        # 최종 분석
        output_lines.extend(_build_final_section(defect_name, relevant))
        output_lines.append("")

        # 최종 리포트 헤더
        output_lines.append("📋 최종 이상분석 리포트")
        output_lines.append(f"   DEFECT: {defect_name}에 대한 레포트를 작성합니다.")

        return "\n".join(output_lines)
