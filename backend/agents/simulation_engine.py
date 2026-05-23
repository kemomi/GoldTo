"""
SimulationEngine — Orchestrates the full GoldTo pipeline:
  1. Graph construction (GraphRAG)
  2. Environment setup (Persona generation)
  3. Simulation (multi-agent interaction)
  4. Report generation
  5. Deep interaction
"""
from __future__ import annotations
import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator, Optional

<<<<<<< HEAD
=======
from openai import AsyncOpenAI

>>>>>>> kemomi/main
from config import settings
from graph.graph_builder import GraphBuilder
from agents.persona_agent import PersonaAgent, generate_personas
from agents.report_agent import ReportAgent
from memory.zep_memory import MemoryManager

<<<<<<< HEAD
# ── LLM 客户端选择（有 Key 用真实，无 Key 用 Mock）────────────────────────────
_MOCK_KEYS = {"", "sk-placeholder", "your_api_key_here", "your_api_key"}

def _is_mock() -> bool:
    key = (settings.llm_api_key or "").strip()
    return key in _MOCK_KEYS or key.startswith("your_")

def _build_llm():
    if _is_mock():
        from utils.mock_client import MockAsyncOpenAI
        print("[LLM] ⚡ Mock 模式已启动（无需 API Key，完整功能体验）")
        return MockAsyncOpenAI()
    else:
        from openai import AsyncOpenAI
        print(f"[LLM] 🌐 连接真实 LLM: {settings.llm_base_url} model={settings.llm_model_name}")
        return AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

=======
>>>>>>> kemomi/main

class SimStatus(str, Enum):
    IDLE = "idle"
    BUILDING_GRAPH = "building_graph"
    GENERATING_PERSONAS = "generating_personas"
    SIMULATING = "simulating"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Session:
    id: str
    prediction_goal: str = ""
    seed_text: str = ""
    status: SimStatus = SimStatus.IDLE
    progress: int = 0          # 0-100
    current_round: int = 0
    total_rounds: int = settings.simulation_rounds
    agents: list[PersonaAgent] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    report: str = ""
    graph_data: dict = field(default_factory=dict)
    graph_summary: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    events: asyncio.Queue = field(default_factory=asyncio.Queue)

    def emit(self, event_type: str, data: dict) -> None:
        """Put an SSE event into the queue."""
        self.events.put_nowait({"type": event_type, "data": data})

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "progress": self.progress,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "prediction_goal": self.prediction_goal,
            "graph_summary": self.graph_summary,
            "agents": [a.to_dict() for a in self.agents],
            "history_count": len(self.history),
            "report": self.report,
            "graph_data": self.graph_data,
            "error": self.error,
        }


class SimulationEngine:
    """Global engine that manages all sessions."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
<<<<<<< HEAD
        self._llm = None
        self._memory: Optional[MemoryManager] = None

    def _get_llm(self):
        if self._llm is None:
            self._llm = _build_llm()
=======
        self._llm: Optional[AsyncOpenAI] = None
        self._memory: Optional[MemoryManager] = None

    def _get_llm(self) -> AsyncOpenAI:
        if self._llm is None:
            self._llm = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )
>>>>>>> kemomi/main
        return self._llm

    def _get_memory(self) -> MemoryManager:
        if self._memory is None:
            self._memory = MemoryManager()
        return self._memory

    # ── Session management ───────────────────────────────────────────────────

    def create_session(self, session_id: str) -> Session:
        session = Session(id=session_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return [s.to_dict() for s in self._sessions.values()]

    # ── Main pipeline ────────────────────────────────────────────────────────

    async def run_pipeline(self, session: Session) -> None:
        """Run the full 5-step pipeline asynchronously."""
        llm = self._get_llm()
        memory = self._get_memory()

        try:
            # ── Step 1: Graph construction ───────────────────────────────────
            session.status = SimStatus.BUILDING_GRAPH
            session.progress = 5
            session.emit("status", {"status": SimStatus.BUILDING_GRAPH, "message": "正在构建知识图谱..."})

            graph_builder = GraphBuilder(llm)
            graph_result = await graph_builder.build(session.seed_text, session.prediction_goal)
            session.graph_data = graph_builder.get_graph_data()
            session.graph_summary = graph_result.get("summary", "")
            session.progress = 20
            session.emit("graph_built", {
                "graph": session.graph_data,
                "summary": session.graph_summary,
                "stats": graph_result["stats"],
            })

            # ── Step 2: Persona generation ───────────────────────────────────
            session.status = SimStatus.GENERATING_PERSONAS
            session.emit("status", {"status": SimStatus.GENERATING_PERSONAS, "message": "正在生成智能体人设..."})

            n_agents = settings.agents_count
            agents = await generate_personas(
                llm,
                summary=session.graph_summary,
                entities=graph_result["entities"],
                goal=session.prediction_goal,
                n=n_agents,
            )
            session.agents = agents

            # Initialize agent memories
            for agent in agents:
                await memory.init_agent(agent.id, {"name": agent.name, "role": agent.role})
                await memory.add_memory(
                    agent.id, "system",
                    f"你是{agent.name}，{agent.role}，工作于{agent.organization}。"
                    f"你正在分析：{session.prediction_goal}。初始立场：{agent.initial_stance:.2f}"
                )

            session.progress = 35
            session.emit("personas_ready", {"agents": [a.to_dict() for a in agents]})

            # ── Step 3: Simulation ────────────────────────────────────────────
            session.status = SimStatus.SIMULATING
            total_rounds = session.total_rounds
            interactions_per_round = max(1, len(agents) // 3)

            for round_num in range(1, total_rounds + 1):
                session.current_round = round_num
                session.emit("round_start", {"round": round_num, "total": total_rounds})

                # Select agent pairs for this round
                pairs = self._select_pairs(agents, interactions_per_round)

                for agent_a, agent_b in pairs:
                    # Get memories
                    mem_a = await memory.get_memory(agent_a.id)
                    graph_ctx = graph_builder.get_context_for_agent(agent_a.role)

                    # Simulate interaction
                    result = await agent_a.interact(
                        agent_b, llm, mem_a, graph_ctx,
                        session.prediction_goal, round_num,
                    )

                    # Store interaction
                    interaction_record = {
                        "round": round_num,
                        "agent_a": agent_a.name,
                        "agent_b": agent_b.name,
                        "agent_a_id": agent_a.id,
                        "agent_b_id": agent_b.id,
                        "dialogue": result.get("dialogue", []),
                        "insight": result.get("my_insight", ""),
                        "action": result.get("action", ""),
                        "stance_before": agent_a.current_stance - result.get("stance_delta", 0),
                        "stance_after": agent_a.current_stance,
                    }
                    session.history.append(interaction_record)

                    # Update memory with interaction summary
                    await memory.add_memory(
                        agent_a.id, "user",
                        f"[回合{round_num}] 与{agent_b.name}交流：{result.get('my_insight', '')}. 行动：{result.get('action', '')}"
                    )

                    # Emit interaction event
                    session.emit("interaction", interaction_record)

                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.2)

                # Update progress
                session.progress = 35 + int(55 * round_num / total_rounds)
                session.emit("round_end", {
                    "round": round_num,
                    "agents": [a.to_dict() for a in agents],
                    "progress": session.progress,
                })

            # ── Step 4: Report generation ─────────────────────────────────────
            session.status = SimStatus.GENERATING_REPORT
            session.progress = 92
            session.emit("status", {"status": SimStatus.GENERATING_REPORT, "message": "正在生成预测报告..."})

            report_agent = ReportAgent(llm)
            report = await report_agent.generate_report(
                goal=session.prediction_goal,
                summary=session.graph_summary,
                agents=agents,
                history=session.history,
                rounds=total_rounds,
            )
            session.report = report
            session.progress = 100
            session.status = SimStatus.COMPLETED

            session.emit("completed", {
                "report": report,
                "agents": [a.to_dict() for a in agents],
                "stats": {
                    "rounds": total_rounds,
                    "interactions": len(session.history),
                    "agents": len(agents),
                },
            })

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[Engine] Pipeline error: {e}\n{tb}")
            session.status = SimStatus.ERROR
            session.error = str(e)
            session.emit("error", {"message": str(e), "detail": tb[:500]})

    # ── Agent interaction ─────────────────────────────────────────────────────

    async def chat(
        self,
        session: Session,
        agent_id: Optional[str],
        message: str,
    ) -> str:
        """Chat with a specific agent or the report agent."""
        llm = self._get_llm()
        report_agent = ReportAgent(llm)
        report_agent.report = session.report
        report_agent.report_summary = session.report[:500]

        if agent_id and agent_id != "report":
            agent = next((a for a in session.agents if a.id == agent_id), None)
            if agent:
                return await report_agent.chat_with_agent(
                    agent.to_dict(), message, session.prediction_goal
                )

        sim_state = f"仿真完成 {len(session.history)} 次互动，{len(session.agents)} 个智能体"
        return await report_agent.chat_with_report(message, session.prediction_goal, sim_state)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _select_pairs(agents: list[PersonaAgent], n: int) -> list[tuple]:
        """Select n agent pairs, preferring agents with opposing stances."""
        if len(agents) < 2:
            return []
        pairs = []
        for _ in range(n):
            # Weighted random: favor agents with fewer interactions
            weights = [1 / (a.interaction_count + 1) for a in agents]
            total = sum(weights)
            probs = [w / total for w in weights]

            idx_a = random.choices(range(len(agents)), weights=probs)[0]
            remaining = [i for i in range(len(agents)) if i != idx_a]
            idx_b = random.choice(remaining)

            pairs.append((agents[idx_a], agents[idx_b]))
        return pairs


# Singleton instance
engine = SimulationEngine()
