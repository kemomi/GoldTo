"""
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

    async def generate_report(
        self,
        goal: str,
        summary: str,
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
