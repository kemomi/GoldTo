"""
ReportAgent — Generates the final strategy brief and answers follow-up questions.
"""
from __future__ import annotations
import json
import re
from openai import AsyncOpenAI
from config import settings

_REPORT_PROMPT = """
你是周大福海外市场战略情报总控 Agent，负责把多个企业专家 Agent 的研判汇总成管理层可用的每日战略简报。

【情报任务】
{goal}

【分析基础】
文档摘要：{summary}
专家 Agent 数量：{agent_count} 个
会商轮次：{rounds} 轮
总会商次数：{interactions} 次

【专家最终判断分布】
{stance_distribution}

【关键洞察摘要】
{insights_summary}

【互动高亮】
{interaction_highlights}

基于以上多 Agent 企业情报会商结果，请生成一份专业、可执行、可追溯的每日海外市场战略简报。

报告结构（用 Markdown 格式，中文）：
1. # 周大福海外市场每日战略简报
2. ## 今日总览
   - 用3-5条概括最重要市场变化
   - 标注机会、风险、待观察
3. ## 高优先级预警
   - 每条包含：市场、事件、影响、优先级、建议负责部门
4. ## 各区域市场变化
   - 东南亚、日韩、北美、中东与澳洲
5. ## 竞品动态
6. ## 产品与消费者趋势
7. ## 渠道与电商机会
8. ## 合规与供应链风险
9. ## 建议行动清单
   - 管理层、海外运营、产品团队、品牌团队、合规法务、供应链分别列出动作
10. ## 信息来源与可信度
   - 说明当前为公开资料/上传材料/模拟信号整合
   - 每条结论给出可信度：高/中/低

要求：
- 必须围绕周大福业务特点：黄金首饰高占比、海外扩张、品牌转型、东南亚/日韩/北美/中东/澳洲、D-ONE、T MARK、Hearts On Fire、传承系列。
- 不要写投资建议，不要预测黄金价格涨跌；要写企业市场情报、风险分级和行动建议。
- 每条建议尽量指向负责部门，并说明为什么今天需要关注。
"""

_CHAT_PROMPT = """
你是周大福海外市场战略情报系统中的战略简报总控 Agent，已完成对「{goal}」的多 Agent 情报会商。

【已有分析报告摘要】
{report_summary}

【当前会商状态】
{sim_state}

用户问题：{question}

请基于简报、会商记录和周大福企业特点，给出专业、可执行、有证据意识的回答。
回答应优先包含：涉及市场、影响判断、建议负责部门、下一步动作、是否需要补充验证来源。
"""

_AGENT_CHAT_PROMPT = """
你正在扮演周大福海外市场战略情报系统中的企业专家 Agent。

【你的身份】
姓名：{name}
职位：{role} @ {organization}
性格：{personality}
当前判断：{stance:.2f}（-1高度风险警惕，+1强机会判断）
动机：{motivation}

【你关于「{goal}」的最新洞察】
{insights}

【用户问题】
{question}

请完全沉浸在企业专家角色中回答，体现你的职能视角、专业背景、机会/风险判断和可执行建议。
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
                    {"role": "system", "content": "你是周大福海外市场战略情报总控 Agent，用中文撰写管理层可用的战略简报。"},
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
                {"role": "system", "content": "你是周大福海外市场战略简报总控 Agent，基于已完成的情报会商回答问题。"},
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
                {"role": "system", "content": f"你是企业专家 Agent {agent_dict['name']}，请完全保持职能视角。"},
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
            f"平均机会/风险判断：{avg:+.3f}",
            f"机会导向（>0.2）：{bullish} 人",
            f"中性观察（-0.2~0.2）：{neutral} 人",
            f"风险警惕（<-0.2）：{bearish} 人",
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
