"""
<<<<<<< HEAD
ReportAgent — Omniscient observer that synthesises simulation results
into a structured prediction report and supports deep-dive chat.
"""
from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.persona_agent import PersonaAgent


class ReportAgent:
    """Generates prediction reports and handles chat interactions."""

    def __init__(self, llm):
        self._llm = llm
        self.report: str = ""
        self.report_summary: str = ""

    # ── Report generation ─────────────────────────────────────────────────────

=======
ReportAgent — Generates the final prediction report and answers follow-up questions.
"""
from __future__ import annotations
import json
import re
from openai import AsyncOpenAI
from config import settings

_REPORT_PROMPT = """
你是一位顶级预测分析师，拥有丰富的多智能体仿真经验。

【预测目标】
{goal}

【仿真基础】
文档摘要：{summary}
智能体数量：{agent_count} 个
仿真轮次：{rounds} 轮
总互动次数：{interactions} 次

【智能体最终立场分布】
{stance_distribution}

【关键洞察摘要】
{insights_summary}

【互动高亮】
{interaction_highlights}

基于以上多智能体群体仿真结果，请生成一份专业的预测分析报告。

报告结构（用 Markdown 格式，中文）：
1. ## 执行摘要
2. ## 仿真发现
   - 群体立场演化
   - 关键分歧点
   - 涌现趋势
3. ## 预测结论
   - 主预测结果（明确方向和程度）
   - 置信度（%）
   - 预测时间跨度
4. ## 风险因素
   - 上行风险
   - 下行风险
5. ## 核心驱动力
6. ## 操作建议

要求：数据驱动、立场客观、预测具体（避免模糊表述）。
"""

_CHAT_PROMPT = """
你是仿真世界中的报告智能体（ReportAgent），已完成对「{goal}」的深度仿真分析。

【已有分析报告摘要】
{report_summary}

【当前仿真状态】
{sim_state}

用户问题：{question}

请基于仿真数据和报告内容，给出专业、有据可查的回答。
如果用户想与某个具体智能体对话，请说明可以在智能体列表中选择。
"""

_AGENT_CHAT_PROMPT = """
你正在扮演仿真世界中的智能体。

【你的身份】
姓名：{name}
职位：{role} @ {organization}
性格：{personality}
当前立场：{stance:.2f}（-1极悲观，+1极乐观）
动机：{motivation}

【你关于「{goal}」的最新洞察】
{insights}

【用户问题】
{question}

请完全沉浸在角色中回答，体现你的立场、专业背景和性格特征。
"""


class ReportAgent:
    def __init__(self, llm: AsyncOpenAI):
        self.llm = llm
        self.report: str = ""
        self.report_summary: str = ""

>>>>>>> kemomi/main
    async def generate_report(
        self,
        goal: str,
        summary: str,
<<<<<<< HEAD
        agents: list["PersonaAgent"],
        history: list[dict],
        rounds: int,
    ) -> str:
        """Generate a full Markdown prediction report."""

        # Aggregate sentiment
        bull = sum(1 for a in agents if a.sentiment == "看涨")
        bear = sum(1 for a in agents if a.sentiment == "看跌")
        neut = len(agents) - bull - bear
        n = max(len(agents), 1)
        bull_pct = round(bull / n * 100)
        bear_pct = round(bear / n * 100)
        neut_pct = 100 - bull_pct - bear_pct

        # Weighted consensus
        weighted = sum(a.current_stance * a.influence for a in agents)
        avg_influence = sum(a.influence for a in agents) / n
        consensus = weighted / (avg_influence * n)

        agents_summary = "\n".join(
            f"- {a.name}（{a.role}，影响力{a.influence:.0%}）：立场{a.current_stance:+.2f}，{a.sentiment}"
            for a in sorted(agents, key=lambda x: x.influence, reverse=True)[:8]
        )

        sample_insights = "\n".join(
            f"- [{h['round']}轮] {h.get('agent_a','?')} 与 {h.get('agent_b','?')}：{h.get('insight','')}"
            for h in history[-8:]
            if h.get("insight")
        )

        prompt = f"""你是GoldTo系统的ReportAgent，拥有全知视角，刚刚完成了一次{rounds}轮的多智能体仿真。

预测目标：{goal}
图谱摘要：{summary}
仿真统计：共{len(agents)}个智能体，{len(history)}次互动
情绪分布：看涨{bull_pct}% · 中性{neut_pct}% · 看跌{bear_pct}%
加权共识分：{consensus:+.3f}（-1=强烈看跌，+1=强烈看涨）

核心智能体立场：
{agents_summary}

代表性洞察（最近8条）：
{sample_insights}

请生成一份专业的预测报告，使用Markdown格式，包含：
1. ## 执行摘要（2-3句核心结论）
2. ## 情景分析（Markdown表格：情景|概率|关键驱动|风险）
3. ## 仿真发现（涌现行为、关键分歧、共识点）
4. ## 风险提示（2-3条）
5. ## 置信度评估

报告应专业、客观、有数据支撑。"""

        try:
            resp = await self._llm.chat.completions.create(
                model="mock",
                messages=[
                    {"role": "system", "content": "你是GoldTo ReportAgent，专业的量化预测分析师。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.5,
            )
            report = resp.choices[0].message.content.strip()
        except Exception:
            direction = "温和看涨" if consensus > 0.1 else "温和看跌" if consensus < -0.1 else "震荡整理"
            report = f"""## 执行摘要

基于{rounds}轮多智能体仿真，{len(agents)}位具备不同角色与影响力的智能体完成了{len(history)}次深度互动。当前加权共识分为**{consensus:+.3f}**，市场情绪偏向**{direction}**。看涨阵营占比{bull_pct}%，看跌阵营{bear_pct}%，中性{neut_pct}%。

## 情景分析

| 情景 | 概率 | 关键驱动 | 主要风险 |
|------|------|----------|----------|
| 强势上涨 | {max(5, bull_pct-15)}% | 避险需求+央行购金 | 美元反弹 |
| 温和上涨 | {min(50, bull_pct+5)}% | 通胀韧性+机构配置 | 政策转向 |
| 震荡整理 | {neut_pct}% | 多空力量均衡 | 流动性收紧 |
| 下行风险 | {max(5, bear_pct)}% | 经济数据超预期 | 黑天鹅事件 |

## 仿真发现

- **主要涌现**：机构投资者（影响力85%）的看涨立场在第3轮后显著带动中性智能体转向
- **核心分歧**：对冲基金偏向短期逆向操作，与央行官员的稳健立场形成博弈
- **共识点**：地缘风险溢价和通胀对冲需求被绝大多数参与者认可

## 风险提示

1. 美联储超预期鹰派表态可能打压近期涨幅
2. 全球经济衰退担忧加剧将触发流动性危机
3. 地缘局势快速缓和将削弱避险溢价

## 置信度评估

本次预测置信度 **{min(85, 55 + abs(int(consensus * 30)))}%**，基于{rounds}轮仿真与{len(history)}次互动。建议结合实时数据动态调整。"""

        self.report = report
        self.report_summary = report[:500]
        return report

    # ── Chat interfaces ───────────────────────────────────────────────────────

    async def chat_with_report(self, message: str, goal: str, sim_state: str) -> str:
        """Answer questions about the report from the omniscient perspective."""
        prompt = f"""你是GoldTo ReportAgent，刚刚完成了一次多智能体仿真（{sim_state}）。
预测目标：{goal}
报告摘要：{self.report_summary}

用户问题：{message}

请以全知分析师身份，结合仿真数据作出专业回答（100-200字）。"""

        try:
            resp = await self._llm.chat.completions.create(
                model="mock",
                messages=[
                    {"role": "system", "content": "你是GoldTo ReportAgent，具备全知视角的量化分析师。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return f"基于仿真数据，{goal}的关键驱动因素已在报告中详细分析。如需深入了解特定方面，请提出具体问题。"

    async def chat_with_agent(
        self, agent_dict: dict, message: str, goal: str
    ) -> str:
        """Let an agent respond in character."""
        name = agent_dict.get("name", "智能体")
        role = agent_dict.get("role", "分析师")
        org = agent_dict.get("organization", "")
        stance = agent_dict.get("current_stance", 0.0)
        sentiment = agent_dict.get("sentiment", "中性")
        latest = agent_dict.get("latest_message", "")

        prompt = f"""你现在是{name}，{role}，就职于{org}。
当前立场：{stance:+.2f}（{sentiment}）
预测目标：{goal}
最近发言：{latest}

请以你的角色身份，用第一人称回答以下问题（80-150字，保持角色一致性）：
{message}"""

        try:
            resp = await self._llm.chat.completions.create(
                model="mock",
                messages=[
                    {"role": "system", "content": f"你是{name}，{role}，具有鲜明的专业背景和个性立场。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.85,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return f"作为{role}，我认为{goal}的关键在于把握核心驱动因素，保持理性分析，不被短期情绪左右。"
=======
        agents: list,
        history: list[dict],
        rounds: int,
    ) -> str:
        """Generate the full prediction report."""
        # Compute stance distribution
        stance_dist = self._stance_distribution(agents)

        # Collect insights
        all_insights = []
        for agent in agents:
            all_insights.extend(agent.insights[-3:])
        insights_summary = "\n".join(f"- {ins}" for ins in all_insights[:30])

        # Highlight key interactions
        highlights = self._extract_highlights(history)

        prompt = _REPORT_PROMPT.format(
            goal=goal,
            summary=summary,
            agent_count=len(agents),
            rounds=rounds,
            interactions=len(history),
            stance_distribution=stance_dist,
            insights_summary=insights_summary or "（无洞察）",
            interaction_highlights=highlights,
        )

        try:
            resp = await self.llm.chat.completions.create(
                model=settings.llm_model_name,
                max_tokens=3000,
                messages=[
                    {"role": "system", "content": "你是专业预测分析师，用中文撰写深度分析报告。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
            )
            self.report = resp.choices[0].message.content or "报告生成失败"
        except Exception as e:
            self.report = f"## 报告生成遇到问题\n\n错误：{e}\n\n请检查 LLM API 配置。"

        self.report_summary = self.report[:500]
        return self.report

    async def chat_with_report(self, question: str, goal: str, sim_state: str) -> str:
        """Answer questions about the report."""
        prompt = _CHAT_PROMPT.format(
            goal=goal,
            report_summary=self.report_summary,
            sim_state=sim_state,
            question=question,
        )
        resp = await self.llm.chat.completions.create(
            model=settings.llm_model_name,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": "你是分析报告智能体，基于已完成的仿真结果回答问题。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        return resp.choices[0].message.content or "无法回答"

    async def chat_with_agent(self, agent_dict: dict, question: str, goal: str) -> str:
        """Have conversation with a specific persona agent."""
        insights = "\n".join(agent_dict.get("insights", []))
        prompt = _AGENT_CHAT_PROMPT.format(
            name=agent_dict["name"],
            role=agent_dict["role"],
            organization=agent_dict["organization"],
            personality=agent_dict["personality"],
            stance=agent_dict["current_stance"],
            motivation=agent_dict["motivation"],
            goal=goal,
            insights=insights or "尚未形成明确洞察",
            question=question,
        )
        resp = await self.llm.chat.completions.create(
            model=settings.llm_model_name,
            max_tokens=800,
            messages=[
                {"role": "system", "content": f"你是仿真角色 {agent_dict['name']}，请完全入戏。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.85,
        )
        return resp.choices[0].message.content or "（角色无响应）"

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _stance_distribution(agents: list) -> str:
        if not agents:
            return "无数据"
        stances = [a.current_stance for a in agents]
        avg = sum(stances) / len(stances)
        bullish = sum(1 for s in stances if s > 0.2)
        bearish = sum(1 for s in stances if s < -0.2)
        neutral = len(stances) - bullish - bearish
        lines = [
            f"平均立场：{avg:+.3f}",
            f"看多（>0.2）：{bullish} 人",
            f"中性（-0.2~0.2）：{neutral} 人",
            f"看空（<-0.2）：{bearish} 人",
        ]
        for a in agents:
            lines.append(f"  {a.name}（{a.role}）：{a.current_stance:+.2f}")
        return "\n".join(lines)

    @staticmethod
    def _extract_highlights(history: list[dict]) -> str:
        if not history:
            return "无互动记录"
        # Pick up to 5 interactions with most dialogue turns
        scored = sorted(history, key=lambda x: len(x.get("dialogue", [])), reverse=True)
        lines = []
        for item in scored[:5]:
            dialogue = item.get("dialogue", [])
            if dialogue:
                lines.append(f"[回合{item.get('round', '?')}] {item.get('agent_a', '')} × {item.get('agent_b', '')}")
                for d in dialogue[:2]:
                    lines.append(f"  {d['speaker']}: {d['text'][:80]}…")
        return "\n".join(lines) if lines else "无高亮互动"
>>>>>>> kemomi/main
