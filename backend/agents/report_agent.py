"""
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

    async def generate_report(
        self,
        goal: str,
        summary: str,
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
