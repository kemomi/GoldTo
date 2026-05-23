"""
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

@dataclass
class PersonaAgent:
    id: str
    name: str
    role: str
    organization: str
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "organization": self.organization,
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
    summary: str,
    entities: list[dict],
    goal: str,
    n: int = 12,
) -> list[PersonaAgent]:
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
