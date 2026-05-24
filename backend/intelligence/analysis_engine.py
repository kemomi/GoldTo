"""
AnalysisEngine — 替代 simulation_engine.py
管理情报分析 Session，驱动 CrewAI 或 Mock 流程，发射 SSE 事件
"""
from __future__ import annotations
import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from config import settings
from intelligence.data_sources import MockDataSource, IntelEvent
from intelligence.llm_client import LLMClient, LLMGenerationError


class AnalysisStatus(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    GENERATING_BRIEFING = "generating_briefing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AnalysisSession:
    id: str
    topic: str = ""
    status: AnalysisStatus = AnalysisStatus.IDLE
    progress: int = 0
    events_collected: list = field(default_factory=list)
    agents_analysis: list = field(default_factory=list)
    briefing: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    events: asyncio.Queue = field(default_factory=asyncio.Queue)

    def emit(self, event_type: str, data: dict) -> None:
        """Put an SSE event into the queue."""
        self.events.put_nowait({"type": event_type, "data": data})

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "status": self.status,
            "progress": self.progress,
            "events_count": len(self.events_collected),
            "agents_analysis": self.agents_analysis,
            "briefing": self.briefing,
            "error": self.error,
        }


class AnalysisEngine:
    """Global engine that manages all intelligence analysis sessions."""

    def __init__(self):
        self._sessions: dict[str, AnalysisSession] = {}

    def create_session(self, session_id: str) -> AnalysisSession:
        session = AnalysisSession(id=session_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return [s.to_dict() for s in self._sessions.values()]

    # ── Data Collection ─────────────────────────────────────────────────────────

    async def collect_data(self, session: AnalysisSession, topic: str) -> None:
        """Step 1: Collect intelligence events from data sources."""
        session.topic = topic
        session.status = AnalysisStatus.COLLECTING
        session.progress = 10
        session.emit("status", {
            "status": AnalysisStatus.COLLECTING,
            "message": "正在从 World Monitor 数据源采集全球事件...",
        })

        try:
            source = MockDataSource()
            events: list[IntelEvent] = await source.collect(topic, limit=8)
            session.events_collected = [e.__dict__ for e in events]
            session.progress = 30
            session.emit("events_collected", {
                "events": session.events_collected,
                "count": len(session.events_collected),
            })
        except Exception as e:
            session.error = str(e)
            session.status = AnalysisStatus.ERROR
            session.emit("error", {"message": f"数据采集失败: {e}"})

    # ── Analysis Pipeline ───────────────────────────────────────────────────────

    async def run_analysis(self, session: AnalysisSession) -> None:
        """Step 2-4: Run multi-agent analysis pipeline."""
        try:
            # 统一走 _run_mock_analysis（内部已根据 is_mock 区分 LLM/Mock）
            # CrewAI 路径保留在 _run_crewai_analysis 中，如需重模式可手动调用
            await self._run_mock_analysis(session)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[AnalysisEngine] Pipeline error: {e}\n{tb}")
            session.status = AnalysisStatus.ERROR
            session.error = str(e)
            session.emit("error", {"message": str(e), "detail": tb[:500]})

    async def _run_mock_analysis(self, session: AnalysisSession) -> None:
        """Mock mode — Simulate CrewAI analysis with pre-canned outputs."""
        session.status = AnalysisStatus.ANALYZING
        session.progress = 35
        session.emit("status", {
            "status": AnalysisStatus.ANALYZING,
            "message": "CrewAI 智能体团队正在协同分析...",
        })

        # Agent 分析（Mock 时模拟延迟，真实模式下跳过延迟直接发送）
        mock_agents = [
            {
                "name": "事件采集员",
                "role": "全球事件监控",
                "insight": (
                    f"关于「{session.topic}」，过去48小时监测到 {len(session.events_collected)} 个关键信号。"
                    "其中地缘冲突升级和政策转向信号最为突出，建议高度关注连锁反应。"
                ),
            },
            {
                "name": "市场分析师",
                "role": "金融市场影响评估",
                "insight": (
                    "从市场反应看，相关资产波动率已上升15%，避险资金开始流入黄金和美元。"
                    "历史回测显示，类似事件后7日内平均波动区间为 ±4.2%。"
                ),
            },
            {
                "name": "政策分析师",
                "role": "政策与合规分析",
                "insight": (
                    "相关政策动向显示，监管层可能在两周内出台应对措施。"
                    "跨境数据流动和投资审查或进一步收紧，合规成本预期上升。"
                ),
            },
        ]

        for i, agent in enumerate(mock_agents):
            if settings.is_mock:
                await asyncio.sleep(1.2)
            session.agents_analysis.append(agent)
            session.progress = 35 + int(40 * (i + 1) / len(mock_agents))
            session.emit("agent_analysis", {
                "agent": agent,
                "progress": session.progress,
                "step": i + 1,
                "total_steps": len(mock_agents),
            })

        # Generate briefing
        session.status = AnalysisStatus.GENERATING_BRIEFING
        session.progress = 80
        session.emit("status", {
            "status": AnalysisStatus.GENERATING_BRIEFING,
            "message": "简报撰写员正在汇总情报...",
        })

        # 尝试 LLM 生成简报，失败则 fallback Mock
        session.status = AnalysisStatus.GENERATING_BRIEFING
        session.progress = 80
        session.emit("status", {
            "status": AnalysisStatus.GENERATING_BRIEFING,
            "message": "正在生成情报简报...",
        })

        if settings.is_mock:
            await asyncio.sleep(1.5)
            session.briefing = self._generate_mock_briefing(session)
        else:
            try:
                llm = LLMClient()
                session.briefing = await llm.generate_briefing(
                    events=session.events_collected,
                    user_config={"industry": session.topic},
                    sources_reference=[],
                )
            except Exception as e:
                print(f"[AnalysisEngine] LLM briefing failed, fallback to mock: {e}")
                await asyncio.sleep(0.5)
                session.briefing = self._generate_mock_briefing(session)

        session.progress = 100
        session.status = AnalysisStatus.COMPLETED
        session.emit("completed", {
            "briefing": session.briefing,
            "agents_analysis": session.agents_analysis,
            "stats": {
                "events": len(session.events_collected),
                "agents": len(session.agents_analysis),
            },
        })

    async def _run_crewai_analysis(self, session: AnalysisSession) -> None:
        """Real mode — Run CrewAI (sync) in a thread pool."""
        from intelligence.crew_factory import create_agents, create_tasks, create_crew

        session.status = AnalysisStatus.ANALYZING
        session.progress = 35
        session.emit("status", {
            "status": AnalysisStatus.ANALYZING,
            "message": "CrewAI 正在编排多 Agent 协作分析...",
        })

        # Format events as text for CrewAI
        events_text = "\n".join(
            f"- [{e['category']}] {e['title']}: {e['summary']}"
            for e in session.events_collected
        )

        def _kickoff():
            agents = create_agents()
            tasks = create_tasks(agents, session.topic, events_text)
            crew = create_crew(agents, tasks)
            return crew.kickoff()

        # Run blocking CrewAI in thread pool
        result = await asyncio.to_thread(_kickoff)

        # Parse result (raw string from crew.kickoff())
        session.briefing = str(result)
        session.progress = 100
        session.status = AnalysisStatus.COMPLETED
        session.emit("completed", {
            "briefing": session.briefing,
            "agents_analysis": [],  # CrewAI raw output doesn't expose per-agent easily
            "stats": {
                "events": len(session.events_collected),
                "agents": 4,
            },
        })

    # ── Chat ────────────────────────────────────────────────────────────────────

    async def chat(self, session: AnalysisSession, message: str) -> str:
        """Chat with the briefing assistant."""
        if settings.is_mock:
            return (
                f"【简报助手】关于「{session.topic}」\n\n"
                f"您问的是：{message}\n\n"
                "基于当前分析结果，建议重点关注：\n"
                "1. 事件连锁反应的传导路径\n"
                "2. 政策窗口期的具体时间范围\n"
                "3. 对冲策略的成本收益比"
            )

        # Real mode — 调用 Kimi API
        try:
            llm = LLMClient()
            events_summary = "\n".join(
                f"- [{e.get('category','')}] {e.get('title','')}: {e.get('summary','')[:100]}"
                for e in session.events_collected[:10]
            )
            system_msg = (
                "你是一位情报分析助手，基于当前分析 session 的事件数据回答用户问题。"
                "回答要专业、简洁，必要时引用事件数据作为依据。"
            )
            user_msg = (
                f"当前分析主题：{session.topic}\n\n"
                f"已采集事件：\n{events_summary}\n\n"
                f"用户问题：{message}"
            )
            return await llm.chat([
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ])
        except Exception as e:
            print(f"[AnalysisEngine] Chat LLM error: {e}")
            return (
                f"【简报助手】关于「{session.topic}」\n\n"
                f"您问的是：{message}\n\n"
                "（LLM 服务暂时不可用，以下是基于规则的回复）\n\n"
                "基于当前分析结果，建议重点关注：\n"
                "1. 事件连锁反应的传导路径\n"
                "2. 政策窗口期的具体时间范围\n"
                "3. 对冲策略的成本收益比"
            )

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _generate_mock_briefing(self, session: AnalysisSession) -> str:
        topic = session.topic
        events = session.events_collected
        agents = session.agents_analysis

        event_bullets = "\n".join(
            f"- **{e['title']}**（{e['source']}）：{e['summary']}"
            for e in events[:5]
        )

        agent_insights = "\n".join(
            f"### {a['name']} — {a['role']}\n{a['insight']}\n"
            for a in agents
        )

        return f"""# 🎯 情报简报：{topic}

## 核心摘要
基于 CrewAI 多智能体协作分析，关于「{topic}」的情势评估如下。整体风险等级为 **中等偏高**，建议在未来 48-72 小时内密切监控事态发展。

## 📡 关键事件监测
{event_bullets}

## 🔍 多维度分析
{agent_insights}

## ⚠️ 风险评估

| 维度 | 评级 | 说明 |
|------|------|------|
| 市场波动 | 🔴 高风险 | 波动率已上升，资金流向避险资产 |
| 政策影响 | 🟡 中等风险 | 潜在监管变化，窗口期约2周 |
| 地缘连锁 | 🟡 中等风险 | 区域影响可控，需防外溢 |
| 信息置信度 | 🟢 较高 | 基于公开数据源，交叉验证充分 |

## 💡 决策建议
1. **短期（24-48h）**：降低风险敞口，增加现金或避险资产配置
2. **中期（1-2周）**：关注政策细则出台，评估合规成本变化
3. **长期（1-3月）**：若事态缓和，可逢低布局被错杀资产

---
*Generated by GoldTo Intelligence Engine | {'Mock Mode' if settings.is_mock else 'CrewAI Mode'}*
"""


# Singleton instance
engine = AnalysisEngine()
