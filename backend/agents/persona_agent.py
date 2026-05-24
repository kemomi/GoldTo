"""
PersonaAgent — Individual agent in the simulation world.
Each agent has: persona, memory, stance, and interaction history.
"""
from __future__ import annotations
import json
import re
import random
from dataclasses import dataclass, field
from typing import Optional
from openai import AsyncOpenAI
from config import settings

_PERSONA_GEN_PROMPT = """
你是周大福海外市场战略情报系统的人设设计师。

基于以下背景信息，生成 {n} 个企业专家 Agent 人设，
这些 Agent 将参与关于「{goal}」的每日海外市场战略情报研判。

文档摘要：{summary}
关键实体：{entities}

要求：
- 必须覆盖以下企业职能视角：金价与汇率风险、区域市场、竞品情报、产品与文化趋势、渠道与电商、合规监管、供应链风险、品牌声誉舆情、战略简报总控。
- 人设要贴合周大福：黄金首饰占比高、海外扩张重点在东南亚/日韩/北美/中东/澳洲、品牌转型、D-ONE、T MARK、Hearts On Fire、传承系列等。
- 每个 Agent 有明确负责市场或职能、可行动的业务动机、对机会/风险的初始判断。
- initial_stance 范围 [-1, 1]：-1=高度风险警惕，0=中性观察，1=强机会判断。

严格返回 JSON 数组，不含任何其他内容：
[
  {{
    "id": "agent_1",
    "name": "林慧敏",
    "role": "东南亚区域市场 Agent",
    "organization": "周大福国际业务部",
    "background": "长期跟踪新加坡、马来西亚、泰国珠宝零售和旅游零售市场",
    "personality": "务实、重视本地文化、机会导向",
    "expertise": ["东南亚零售", "机场店", "华人消费", "旅游零售"],
    "initial_stance": 0.35,
    "motivation": "识别海外市场机会，帮助区域团队制定门店、产品和营销动作"
  }}
]
"""

_INTERACTION_PROMPT = """
你正在扮演周大福海外战略情报系统中的企业专家 Agent，请保持角色一致性。

【你的身份】
姓名：{name}
职位：{role} @ {organization}
性格：{personality}
专业：{expertise}
当前判断（-1高度风险警惕~+1强机会判断）：{stance:.2f}
动机：{motivation}

【你的记忆】
{memory}

【知识图谱上下文】
{graph_context}

【情报任务】
{goal}

【当前情景】
回合 {round_num}，你与 {other_name}（{other_role}）进行了一次企业情报会商。

请生成这次互动的内容，包含：
1. 真实的业务对话（3-5轮），围绕市场变化、机会/风险、负责部门、行动建议展开。
2. 互动后你的判断变化、关键洞察和建议动作。
3. 如果涉及事实判断，应强调需要来源、时间和可信度。

严格返回 JSON，不含 markdown：
{{
  "dialogue": [
    {{"speaker": "{name}", "text": "..."}},
    {{"speaker": "{other_name}", "text": "..."}}
  ],
  "my_insight": "通过这次交流，我意识到...",
  "stance_delta": 0.05,
  "action": "基于这次交流，我建议..."
}}
"""


@dataclass
class PersonaAgent:
    id: str
    name: str
    role: str
    organization: str
    background: str
    personality: str
    expertise: list[str]
    initial_stance: float
    motivation: str

    # Runtime state
    current_stance: float = field(init=False)
    interaction_count: int = field(default=0, init=False)
    insights: list[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.current_stance = self.initial_stance

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "organization": self.organization,
            "background": self.background,
            "personality": self.personality,
            "expertise": self.expertise,
            "initial_stance": self.initial_stance,
            "current_stance": self.current_stance,
            "motivation": self.motivation,
            "interaction_count": self.interaction_count,
            "insights": self.insights[-5:],
        }

    async def interact(
        self,
        other: "PersonaAgent",
        llm: AsyncOpenAI,
        memory: str,
        graph_context: str,
        goal: str,
        round_num: int,
    ) -> dict:
        prompt = _INTERACTION_PROMPT.format(
            name=self.name,
            role=self.role,
            organization=self.organization,
            personality=self.personality,
            expertise=", ".join(self.expertise),
            stance=self.current_stance,
            motivation=self.motivation,
            memory=memory,
            graph_context=graph_context,
            goal=goal,
            round_num=round_num,
            other_name=other.name,
            other_role=other.role,
        )
        try:
            resp = await llm.chat.completions.create(
                model=settings.llm_model_name,
                max_tokens=settings.max_tokens,
                messages=[
                    {"role": "system", "content": "你是周大福海外市场战略情报系统中的企业专家 Agent，严格按人设行事，只返回合法 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
            )
            raw = resp.choices[0].message.content or "{}"
            result = self._parse_json(raw)
        except Exception as e:
            print(f"[Agent:{self.name}] LLM error: {e}")
            result = {
                "dialogue": [{"speaker": self.name, "text": "（通信中断）"}],
                "my_insight": "无法建立联系",
                "stance_delta": 0.0,
                "action": "继续观察",
            }

        # Update agent state
        delta = float(result.get("stance_delta", 0.0))
        self.current_stance = max(-1.0, min(1.0, self.current_stance + delta))
        self.interaction_count += 1
        insight = result.get("my_insight", "")
        if insight:
            self.insights.append(insight)

        return result

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return {"dialogue": [], "my_insight": "", "stance_delta": 0.0, "action": ""}


async def generate_personas(
    llm: AsyncOpenAI,
    summary: str,
    entities: list[dict],
    goal: str,
    n: int = 12,
) -> list[PersonaAgent]:
    """Use LLM to generate N diverse agent personas."""
    entity_desc = ", ".join(e["name"] for e in entities[:20])
    prompt = _PERSONA_GEN_PROMPT.format(
        n=n, goal=goal, summary=summary, entities=entity_desc
    )
    try:
        resp = await llm.chat.completions.create(
            model=settings.llm_model_name,
            max_tokens=settings.max_tokens,
            messages=[
                {"role": "system", "content": "你是人设设计专家，只返回合法 JSON 数组，不含任何 markdown 或说明文字。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
        )
        raw = resp.choices[0].message.content or "[]"
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

        # Handle possible wrapping object
        if cleaned.startswith("{"):
            data = json.loads(cleaned)
            personas_data = data.get("agents") or data.get("personas") or list(data.values())[0]
        else:
            personas_data = json.loads(cleaned)

        agents = []
        for i, p in enumerate(personas_data[:n]):
            agents.append(PersonaAgent(
                id=p.get("id", f"agent_{i+1}"),
                name=p.get("name", f"智能体{i+1}"),
                role=p.get("role", "分析师"),
                organization=p.get("organization", "未知机构"),
                background=p.get("background", ""),
                personality=p.get("personality", "理性"),
                expertise=p.get("expertise", []),
                initial_stance=float(p.get("initial_stance", random.uniform(-0.3, 0.3))),
                motivation=p.get("motivation", ""),
            ))
        print(f"[Personas] Generated {len(agents)} agents")
        return agents

    except Exception as e:
        print(f"[Personas] Generation failed: {e}")
        # Return fallback personas
        return _fallback_personas(n)


def _fallback_personas(n: int) -> list[PersonaAgent]:
    templates = [
        ("林慧敏", "东南亚区域市场 Agent", "周大福国际业务部", 0.42, ["东南亚零售", "机场店", "华人消费"]),
        ("金志贤", "日韩市场 Agent", "周大福国际业务部", 0.18, ["日本珠宝消费", "韩国潮流", "设计趋势"]),
        ("Olivia Chan", "北美市场 Agent", "周大福国际业务部", 0.08, ["北美华人市场", "高端商圈", "品牌认知"]),
        ("Ahmed Wong", "中东与澳洲新市场 Agent", "周大福战略拓展组", 0.36, ["迪拜", "多哈", "澳大利亚", "市场进入"]),
        ("许嘉仪", "金价与汇率风险 Agent", "集团财务与风险管理部", -0.22, ["国际金价", "汇率", "定价"]),
        ("陈柏森", "竞品情报 Agent", "品牌战略部", -0.10, ["Cartier", "Tiffany", "六福珠宝", "门店拓展"]),
        ("周雅琪", "产品与文化趋势 Agent", "产品创新中心", 0.30, ["古法黄金", "婚嫁珠宝", "D-ONE", "Hearts On Fire"]),
        ("Tan Wei", "渠道与电商平台 Agent", "全渠道零售部", 0.24, ["Shopee", "Lazada", "Rakuten", "机场零售"]),
        ("黄谨言", "合规与监管 Agent", "法务合规部", -0.35, ["贵金属认证", "AML", "数据隐私", "广告合规"]),
        ("梁思远", "供应链风险 Agent", "供应链管理部", -0.18, ["钻石溯源", "T MARK", "物流", "ESG"]),
        ("何婉莹", "品牌声誉与舆情 Agent", "公关传播部", -0.12, ["社媒舆情", "服务评价", "代言人风险"]),
        ("郑启明", "战略简报总控 Agent", "管理层办公室", 0.05, ["战略简报", "跨部门协同", "行动清单"]),
    ]
    return [
        PersonaAgent(
            id=f"agent_{i+1}",
            name=t[0],
            role=t[1],
            organization=t[2],
            background=f"{t[0]}在{t[2]}负责周大福海外市场相关情报研判，熟悉企业出海、珠宝零售和跨市场协同。",
            personality="理性、务实、强调证据链和可执行动作",
            expertise=t[4],
            initial_stance=t[3],
            motivation="将公开市场信号转化为机会、风险和部门行动建议",
        )
        for i, t in enumerate(templates[:n])
    ]
