"""
상위 Agent 모듈: 이상분석 Agent

역할:
  - DEFECT 명 기준으로 관련 공정을 식별
  - 각 공정(중간 Agent)의 판단 결과를 수집
  - 이상이 있는 공정과 근본 원인을 종합하여 최종 리포트 생성
"""

from __future__ import annotations
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage


def _make_llm(model: str = "gemma3:4b"):
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0)
    except Exception as e:
        raise RuntimeError(f"Ollama LLM 초기화 실패: {e}") from e


class UpperAgent:
    """
    이상분석 상위 Agent.
    중간 Agent 결과를 종합하여 최종 DEFECT 분석 리포트를 생성합니다.
    """

    # DEFECT → 관련 공정 매핑 (테스트용 간이 규칙)
    DEFECT_PROCESS_MAP: dict[str, list[str]] = {
        "파티클":      ["PHT", "DRY", "CVD"],
        "CD불량":      ["PHT", "DRY", "SPT"],
        "두께불량":    ["CVD", "WET"],
        "결함":        ["PHT", "CVD", "WET"],
        "스크래치":    ["WET", "SPT"],
        "오염":        ["PHT", "DRY", "WET"],
        "default":     ["PHT", "DRY", "CVD", "SPT", "WET"],
    }

    def __init__(self, model: str = "gemma3:4b"):
        self.llm = _make_llm(model)

    def _get_related_processes(self, defect_name: str) -> list[str]:
        """DEFECT 명에서 관련 공정 목록을 반환합니다."""
        for key in self.DEFECT_PROCESS_MAP:
            if key in defect_name:
                return self.DEFECT_PROCESS_MAP[key]
        return self.DEFECT_PROCESS_MAP["default"]

    def run(
        self,
        defect_name: str,
        lot_id: str,
        middle_results: dict[str, dict],
    ) -> str:
        """
        중간 Agent 결과를 종합하여 최종 리포트 문자열을 반환합니다.
        """
        print(f"\n{'='*60}")
        print(f"[이상분석 Agent] DEFECT='{defect_name}', LOT='{lot_id}' 최종 분석 중...")

        related = self._get_related_processes(defect_name)
        print(f"  관련 공정: {related}")

        # 관련 공정만 필터링
        relevant = {p: v for p, v in middle_results.items() if p in related}

        # 이상 공정 추출
        abnormal_processes = {p: v for p, v in relevant.items() if v.get("is_abnormal")}
        normal_processes   = {p: v for p, v in relevant.items() if not v.get("is_abnormal")}

        # 요약 텍스트 작성
        summary_lines = ["[공정별 분석 결과]"]
        for p, v in relevant.items():
            icon = "⚠ 이상" if v["is_abnormal"] else "✓ 정상"
            summary_lines.append(f"  {p}: {icon} → {v['reason']}")

        # 하위 분석 상세 추가
        summary_lines.append("\n[하위 분석 상세]")
        for p, v in relevant.items():
            for agent_name, lr in v.get("lower_results", {}).items():
                icon = "⚠" if lr["is_abnormal"] else "✓"
                tool_info = " | ".join(
                    f"{t['tool']}:{t['result']}" for t in lr.get("tool_results", [])
                )
                summary_lines.append(
                    f"  {p}/{agent_name} {icon} [{tool_info}] → {lr['reason']}"
                )

        summary_text = "\n".join(summary_lines)

        system_prompt = (
            "당신은 반도체 DEFECT 분석 전문가입니다. "
            "여러 공정의 분석 결과를 종합하여 DEFECT의 근본 원인을 진단하세요. "
            "답변은 한국어로, 다음 구조를 따르세요:\n"
            "1. 요약 (2~3 문장)\n"
            "2. 이상 공정 목록 및 원인\n"
            "3. 결론 및 조치 권고"
        )
        user_prompt = (
            f"DEFECT 명: {defect_name}\n"
            f"LOT ID: {lot_id}\n\n"
            f"{summary_text}\n\n"
            "위 정보를 바탕으로 최종 분석 리포트를 작성해 주세요."
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            llm_report = response.content.strip()
        except Exception as e:
            llm_report = f"LLM 리포트 생성 실패: {e}"

        # 최종 리포트 조립
        separator = "=" * 60
        report_parts = [
            separator,
            f"📋 최종 이상분석 리포트",
            f"   DEFECT: {defect_name} | LOT: {lot_id}",
            separator,
            summary_text,
            "",
            "─" * 60,
            "🔍 LLM 종합 분석",
            "─" * 60,
            llm_report,
            separator,
        ]
        final_report = "\n".join(report_parts)
        print(final_report)
        return final_report
