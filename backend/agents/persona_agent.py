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
你是一个多智能体仿真系统的人设设计师。

基于以下背景信息，生成 {n} 个多样化的仿真智能体人设，
这些智能体将参与关于「{goal}」的预测推演。

文档摘要：{summary}
关键实体：{entities}

要求：
- 人设涵盖不同立场（乐观/悲观/中立）
- 职业多元化（分析师、交易员、政策制定者、记者、学者、企业高管等）
- 有具体的背景故事和利益关系
- 立场数值 stance 范围 [-1, 1]（-1=极度悲观, 0=中立, 1=极度乐观）

严格返回 JSON 数组，不含任何其他内容：
[
  {{
    "id": "agent_1",
    "name": "张伟",
    "role": "黄金期货分析师",
    "organization": "中国国际金融股份有限公司",
    "background": "...",
    "personality": "理性、数据驱动、偏保守",
    "expertise": ["黄金市场", "期货合约", "宏观经济"],
    "initial_stance": 0.3,
    "motivation": "维护客户资产安全，追求稳健收益"
  }}
]
"""

_INTERACTION_PROMPT = """
你正在扮演仿真世界中的智能体，请保持角色一致性。

【你的身份】
姓名：{name}
职位：{role} @ {organization}
性格：{personality}
专业：{expertise}
当前立场（-1悲观~+1乐观）：{stance:.2f}
动机：{motivation}

【你的记忆】
{memory}

【知识图谱上下文】
{graph_context}

【预测目标】
{goal}

【当前情景】
回合 {round_num}，你与 {other_name}（{other_role}）进行了一次交流。

请生成这次互动的内容，包含：
1. 真实的对话（3-5轮）
2. 互动后你的立场变化和关键洞察

严格返回 JSON，不含 markdown：
{{
  "dialogue": [
    {{"speaker": "{name}", "text": "..."}},
    {{"speaker": "{other_name}", "text": "..."}}
  ],
  "my_insight": "通过这次交流，我意识到...",
  "stance_delta": 0.05,
  "action": "基于这次交流，我决定..."
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
                    {"role": "system", "content": "你是多智能体仿真系统中的一个角色，严格按人设行事，只返回合法 JSON。"},
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
        ("张伟", "宏观经济分析师", "研究院", 0.3),
        ("李娜", "期货交易员", "证券公司", -0.2),
        ("王强", "央行政策研究员", "央行", 0.1),
        ("陈静", "国际贸易专家", "商务部", 0.0),
        ("刘洋", "地缘政治分析师", "智库", -0.4),
        ("赵磊", "科技企业CEO", "科技公司", 0.5),
        ("周雪", "媒体记者", "财经媒体", 0.0),
        ("吴刚", "私募基金经理", "私募基金", 0.6),
        ("钱芳", "学术经济学家", "大学", -0.1),
        ("孙浩", "大宗商品交易商", "贸易公司", 0.2),
        ("马云", "供应链专家", "物流企业", 0.0),
        ("徐敏", "风险评估师", "评级机构", -0.3),
    ]
    return [
        PersonaAgent(
            id=f"agent_{i+1}",
            name=t[0],
            role=t[1],
            organization=t[2],
            background=f"{t[0]}在{t[2]}工作多年，专注于市场分析。",
            personality="理性、客观",
            expertise=["市场分析"],
            initial_stance=t[3],
            motivation="追求准确的市场判断",
        )
        for i, t in enumerate(templates[:n])
    ]
