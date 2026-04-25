# 🏭 반도체 공정 DEFECT 다중 Agent 분석 시스템

Ollama + LangChain + LangGraph 를 사용한 3계층 다중 Agent 파이프라인입니다.

---

## 📁 프로젝트 구조

```
defect_analysis_agent/
├── main.py                  # 실행 진입점 (Ollama 사용)
├── test_mock.py             # Mock LLM 테스트 (Ollama 없이 동작)
│
├── tools/
│   └── mcp_tools.py         # MCP Tool 4종 (TREND / MAP / FDC / 설비이력)
│
├── agents/
│   ├── lower_agents.py      # 하위 Agent: EQP / Chamber / Layer / MODEL
│   ├── middle_agents.py     # 중간 Agent: PHT / DRY / CVD / SPT / WET
│   └── upper_agent.py       # 상위 Agent: 이상분석
│
└── graph/
    ├── state.py             # LangGraph 공유 상태 정의
    └── pipeline.py          # LangGraph 파이프라인 (노드 & 엣지)
```

---

## 🔄 Agent 계층 구조

```
[입력] DEFECT명 + LOT ID
        │
        ▼
┌─────────────────────────────────────────────────┐
│  상위 Agent: 이상분석                            │
│  · 중간 Agent 결과 종합 → 최종 리포트 생성      │
└────────────────┬────────────────────────────────┘
                 │  결과 전달
    ┌────────────┴──────────────────────────────┐
    │  중간 Agent (공정별 5종)                   │
    │  PHT / DRY / CVD / SPT / WET              │
    │  · 하위 Agent 4종을 순서대로 호출           │
    │  · 공정 이상 여부 판단 후 상위에 보고       │
    └────────────┬──────────────────────────────┘
                 │  결과 전달
    ┌────────────┴──────────────────────────────┐
    │  하위 Agent (분석 단계별 4종)              │
    │  EQP / Chamber / Layer / MODEL            │
    │  · MCP Tool 호출 → 이상 유무 판단          │
    └────────────┬──────────────────────────────┘
                 │  Tool 호출
    ┌────────────┴──────────────────────────────┐
    │  MCP Tools (4종)                          │
    │  TREND / MAP / FDC / 설비이력             │
    │  · 지정 리스트에서 랜덤값 반환             │
    └───────────────────────────────────────────┘
```

---

## 🛠 Tool 리스트값

| Tool    | 이상 판정 값 (나머지는 정상)              |
|---------|------------------------------------------|
| TREND   | 상승, 산포증가, 헌팅, 급증               |
| MAP     | 특이 MAP 있음, 군집 MAP, 코너 MAP, 하단 MAP |
| FDC     | 이상있음                                 |
| 설비이력 | FDC 알람, Error, BM                     |

---

## ▶ 실행 방법

### 1. 테스트 (Mock LLM - Ollama 없이)
```bash
cd defect_analysis_agent
python test_mock.py
```

### 2. 실제 실행 (Ollama 필요)
```bash
# Ollama 설치 후 모델 다운로드
ollama pull gemma3:4b

# 실행
python main.py 파티클 LOT-001
python main.py CD불량 LOT-042 gemma3:4b
```

### 3. Python API
```python
from graph.pipeline import run_analysis

report = run_analysis(
    defect_name="파티클",
    lot_id="LOT-001",
    model="gemma3:4b",   # 기본값
)
print(report)
```

---

## ⚙ 지원 DEFECT → 공정 매핑

| DEFECT  | 관련 공정          |
|---------|--------------------|
| 파티클  | PHT, DRY, CVD      |
| CD불량  | PHT, DRY, SPT      |
| 두께불량 | CVD, WET          |
| 결함    | PHT, CVD, WET      |
| 스크래치 | WET, SPT          |
| 오염    | PHT, DRY, WET      |
| 기타    | PHT, DRY, CVD, SPT, WET (전체) |

---

## 📦 의존성

```bash
pip install langchain langgraph langchain-community langchain-ollama
```
