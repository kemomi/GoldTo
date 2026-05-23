"""
<<<<<<< HEAD
PersonaAgent — Individual agent with personality, memory, and interaction logic.
generate_personas — Factory function to create a diverse set of agents.
"""
from __future__ import annotations
import json
import random
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


# ── Archetype definitions ─────────────────────────────────────────────────────

ARCHETYPES = [
    {"role": "央行官员",    "influence": 0.95, "bias": 0.0,   "org": "中央银行"},
    {"role": "政策制定者",  "influence": 0.90, "bias": 0.05,  "org": "财政部"},
    {"role": "机构投资者",  "influence": 0.85, "bias": 0.15,  "org": "养老基金"},
    {"role": "对冲基金",    "influence": 0.80, "bias": 0.25,  "org": "对冲基金公司"},
    {"role": "地缘分析师",  "influence": 0.65, "bias": 0.10,  "org": "智库研究院"},
    {"role": "媒体分析师",  "influence": 0.60, "bias": 0.20,  "org": "财经媒体"},
    {"role": "商品交易员",  "influence": 0.55, "bias": 0.30,  "org": "期货交易所"},
    {"role": "散户交易者",  "influence": 0.30, "bias": 0.40,  "org": "个人投资者"},
]

_CN_SURNAMES = "赵钱孙李周吴郑王冯陈楚魏蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜谢邹喻柏水窦章云苏潘葛奚范彭郎"
_CN_GIVEN   = "浩明轩宇博文涛伟晨昊峰磊鹏飞帆辉斌志强刚勇华超云珊慧颖婷雯欣芳倩静宁"

_NAMES_POOL: list[str] = []
for s in _CN_SURNAMES:
    for g in _CN_GIVEN[:20]:
        _NAMES_POOL.append(s + g)
random.shuffle(_NAMES_POOL)


def _random_name(exclude: set) -> str:
    for n in _NAMES_POOL:
        if n not in exclude:
            return n
    return "匿名" + str(random.randint(100, 999))


# ── PersonaAgent ──────────────────────────────────────────────────────────────
=======
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

>>>>>>> kemomi/main

@dataclass
class PersonaAgent:
    id: str
    name: str
    role: str
    organization: str
<<<<<<< HEAD
    influence: float          # 0-1, affects sentiment propagation
    initial_stance: float     # -1 (bear) to +1 (bull)
    current_stance: float = 0.0
    sentiment: str = "中性"
    confidence: float = 0.5
    latest_message: str = ""
    interaction_count: int = 0
    memory_summary: str = ""

    def __post_init__(self):
        if self.current_stance == 0.0:
            self.current_stance = self.initial_stance
        self._update_sentiment()

    def _update_sentiment(self):
        if self.current_stance > 0.2:
            self.sentiment = "看涨"
        elif self.current_stance < -0.2:
            self.sentiment = "看跌"
        else:
            self.sentiment = "中性"

    async def interact(
        self,
        other: "PersonaAgent",
        llm,
        memory: list[dict],
        graph_ctx: str,
        goal: str,
        round_num: int,
    ) -> dict:
        """Simulate a dialogue with another agent; update stance."""
        mem_text = "\n".join(
            f"[{m['role']}] {m['content']}" for m in memory[-4:]
        ) if memory else "（无历史记忆）"

        prompt = f"""你是{self.name}，{self.role}，就职于{self.organization}。
当前分析目标：{goal}
你的当前立场分值：{self.current_stance:.2f}（-1=强烈看跌，0=中性，+1=强烈看涨）
对方：{other.name}，{other.role}（立场：{other.current_stance:.2f}）
知识图谱背景：{graph_ctx[:300]}
近期记忆：{mem_text[:400]}
当前回合：{round_num}

请用JSON格式输出本次互动结果：
{{
  "dialogue": [
    {{"speaker": "{self.name}", "text": "你的发言（1-2句，专业且有个性）"}},
    {{"speaker": "{other.name}", "text": "对方可能的回应（1句）"}}
  ],
  "my_insight": "本次互动后你的核心洞察（1句）",
  "action": "你决定采取的行动（1句，如：增持/减仓/观望/发布研报等）",
  "stance_delta": 0.05,
  "confidence_delta": 0.02
}}
只返回JSON。"""

        try:
            resp = await llm.chat.completions.create(
                model="mock",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.85,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
            result = json.loads(raw)
        except Exception:
            result = {
                "dialogue": [
                    {"speaker": self.name, "text": f"从{self.role}角度看，当前形势需谨慎分析。"},
                    {"speaker": other.name, "text": "同意，市场信号较为复杂。"},
                ],
                "my_insight": "需综合多方信号再做判断。",
                "action": "保持观望，等待更多数据。",
                "stance_delta": random.uniform(-0.1, 0.1),
                "confidence_delta": random.uniform(-0.05, 0.05),
            }

        # Apply stance change (clamp to [-1, 1])
        delta = float(result.get("stance_delta", 0))
        self.current_stance = max(-1.0, min(1.0, self.current_stance + delta))
        self.confidence = max(0.0, min(1.0, self.confidence + float(result.get("confidence_delta", 0))))
        self._update_sentiment()

        dialogue = result.get("dialogue", [])
        if dialogue:
            self.latest_message = dialogue[0].get("text", "")

        self.interaction_count += 1
        return result
=======
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
>>>>>>> kemomi/main

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "organization": self.organization,
<<<<<<< HEAD
            "influence": self.influence,
            "initial_stance": round(self.initial_stance, 3),
            "current_stance": round(self.current_stance, 3),
            "sentiment": self.sentiment,
            "confidence": round(self.confidence, 3),
            "latest_message": self.latest_message,
            "interaction_count": self.interaction_count,
        }


# ── Persona factory ───────────────────────────────────────────────────────────

async def generate_personas(
    llm,
=======
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
>>>>>>> kemomi/main
    summary: str,
    entities: list[dict],
    goal: str,
    n: int = 12,
) -> list[PersonaAgent]:
<<<<<<< HEAD
    """Generate n PersonaAgents appropriate for the given context."""

    prompt = f"""为以下预测场景生成{n}个具有独特人格的智能体，以JSON数组返回：
预测目标：{goal}
场景摘要：{summary[:500]}
关键实体：{', '.join(e['label'] for e in entities[:6])}

每个智能体格式：
{{
  "name": "中文姓名",
  "role": "角色类型（从以下选择：央行官员/政策制定者/机构投资者/对冲基金/地缘分析师/媒体分析师/商品交易员/散户交易者）",
  "organization": "所属机构",
  "initial_stance": 0.3,
  "influence": 0.75
}}

确保角色多样（涵盖不同类型），initial_stance范围-1到+1，influence范围0到1。
只返回JSON数组。"""

    agents: list[PersonaAgent] = []
    used_names: set[str] = set()

    try:
        resp = await llm.chat.completions.create(
            model="mock",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.9,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)

        for item in data[:n]:
            name = item.get("name", _random_name(used_names))
            used_names.add(name)
            role = item.get("role", "机构投资者")
            arch = next((a for a in ARCHETYPES if a["role"] == role), ARCHETYPES[2])
            stance = float(item.get("initial_stance", arch["bias"] + random.uniform(-0.2, 0.2)))
            stance = max(-1.0, min(1.0, stance))
            agents.append(PersonaAgent(
                id=f"agent_{len(agents):03d}",
                name=name,
                role=role,
                organization=item.get("organization", arch["org"]),
                influence=float(item.get("influence", arch["influence"])),
                initial_stance=stance,
                confidence=0.5 + arch["influence"] * 0.3,
            ))
    except Exception:
        pass

    # Fill remaining with archetype-based defaults
    arch_cycle = list(ARCHETYPES) * ((n // len(ARCHETYPES)) + 2)
    while len(agents) < n:
        arch = arch_cycle[len(agents) % len(ARCHETYPES)]
        name = _random_name(used_names)
        used_names.add(name)
        stance = arch["bias"] + random.uniform(-0.25, 0.25)
        stance = max(-1.0, min(1.0, stance))
        agents.append(PersonaAgent(
            id=f"agent_{len(agents):03d}",
            name=name,
            role=arch["role"],
            organization=arch["org"],
            influence=arch["influence"] + random.uniform(-0.05, 0.05),
            initial_stance=stance,
            confidence=0.4 + arch["influence"] * 0.35,
        ))

    return agents[:n]
=======
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
>>>>>>> kemomi/main
