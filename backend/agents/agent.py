"""Individual agent with unique persona, memory, and behavior."""
import random, hashlib, json
from dataclasses import dataclass, field
from typing import Optional
from utils.llm_client import llm

AGENT_ARCHETYPES = [
    {"type": "institutional_investor", "label": "机构投资者",
     "traits": ["理性", "数据驱动", "长线思维", "风险厌恶"],
     "influence": 0.85},
    {"type": "retail_trader",          "label": "散户交易者",
     "traits": ["情绪化", "短线导向", "跟风", "贪婪/恐惧"],
     "influence": 0.30},
    {"type": "policy_maker",           "label": "政策制定者",
     "traits": ["保守", "系统性思维", "信息滞后", "公众压力"],
     "influence": 0.90},
    {"type": "media_analyst",          "label": "媒体分析师",
     "traits": ["叙事驱动", "放大效应", "快速传播", "情绪化"],
     "influence": 0.60},
    {"type": "hedge_fund_manager",     "label": "对冲基金经理",
     "traits": ["逆向思维", "高杠杆", "信息优势", "短期博弈"],
     "influence": 0.80},
    {"type": "central_banker",         "label": "央行官员",
     "traits": ["稳定优先", "货币工具", "信号博弈", "全局视角"],
     "influence": 0.95},
    {"type": "geopolitical_analyst",   "label": "地缘政治分析师",
     "traits": ["风险感知", "历史类比", "非线性思维"],
     "influence": 0.65},
    {"type": "commodity_trader",       "label": "大宗商品交易员",
     "traits": ["技术分析", "供需敏感", "杠杆操作", "短视"],
     "influence": 0.55},
]

BULLISH  = "看涨"
BEARISH  = "看跌"
NEUTRAL  = "中性"


@dataclass
class AgentMemory:
    short_term: list[str] = field(default_factory=list)   # last 10 events
    long_term:  list[str] = field(default_factory=list)    # important memories
    sentiment_history: list[str] = field(default_factory=list)

    def add(self, event: str, important: bool = False):
        self.short_term.append(event)
        if len(self.short_term) > 10:
            self.short_term.pop(0)
        if important:
            self.long_term.append(event)
            if len(self.long_term) > 30:
                self.long_term.pop(0)

    def get_recent(self, n: int = 5) -> str:
        return "\n".join(self.short_term[-n:]) if self.short_term else "无历史记忆"


class Agent:
    def __init__(self, agent_id: str, archetype: dict, name: str,
                 background: str = "", graph_context: str = ""):
        self.id           = agent_id
        self.archetype    = archetype
        self.name         = name
        self.background   = background
        self.graph_context = graph_context
        self.memory       = AgentMemory()
        self.sentiment    = NEUTRAL
        self.confidence   = random.uniform(0.4, 0.9)
        self.wealth_level = random.uniform(0.3, 1.0)
        self.action_log: list[dict] = []
        # personality seed for reproducibility
        seed = int(hashlib.md5(agent_id.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)

    # ─── core loop ─────────────────────────────────────────────────────────
    def perceive_and_react(self, world_event: str, round_num: int,
                           peer_sentiments: list[str]) -> dict:
        """Process world event and produce reaction."""
        system = self._build_system_prompt()
        peer_info = "、".join(peer_sentiments[:5]) if peer_sentiments else "未知"
        user_msg = (
            f"【第{round_num}轮模拟】\n"
            f"世界事件：{world_event}\n"
            f"周围参与者情绪：{peer_info}\n"
            f"你的近期记忆：\n{self.memory.get_recent()}\n\n"
            f"请以你的身份做出反应（不超过150字），并给出：\n"
            f"1. 你的情绪立场（看涨/看跌/中性）\n"
            f"2. 你的具体行为\n"
            f"3. 对其他参与者的影响\n"
            f"返回JSON：{{\"sentiment\":\"看涨|看跌|中性\",\"action\":\"行为描述\","
            f"\"message\":\"公开发言\",\"influence_score\":0.0-1.0}}"
        )
        result = llm.json_chat([{"role": "user", "content": user_msg}], system=system)

        # Normalise
        if "sentiment" not in result:
            result = {
                "sentiment": random.choice([BULLISH, BEARISH, NEUTRAL]),
                "action": "观望市场",
                "message": f"作为{self.name}，我正在评估形势。",
                "influence_score": self.archetype["influence"] * self.confidence,
            }
        self.sentiment = result.get("sentiment", NEUTRAL)
        self.memory.add(f"R{round_num}: {result.get('action','')}", important=round_num % 5 == 0)
        self.memory.sentiment_history.append(self.sentiment)
        self.action_log.append({"round": round_num, **result})
        return result

    def chat(self, user_message: str, context: str = "") -> str:
        """Interactive chat with this agent."""
        system = self._build_system_prompt()
        msgs = [{"role": "user", "content":
                 f"背景信息：{context}\n\n用户问题：{user_message}\n\n"
                 f"请以{self.name}的身份自然地回答（不超过200字）"}]
        return llm.chat(msgs, system=system, temperature=0.9)

    # ─── helpers ───────────────────────────────────────────────────────────
    def _build_system_prompt(self) -> str:
        traits = "、".join(self.archetype["traits"])
        return (
            f"你扮演{self.name}，一位{self.archetype['label']}。\n"
            f"性格特征：{traits}\n"
            f"背景：{self.background}\n"
            f"当前情绪立场：{self.sentiment}\n"
            f"置信度：{self.confidence:.0%}\n"
            f"相关知识背景：\n{self.graph_context}\n\n"
            f"请始终保持角色一致性，用中文回答，语言风格符合该角色身份。"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.archetype["type"],
            "label": self.archetype["label"],
            "traits": self.archetype["traits"],
            "sentiment": self.sentiment,
            "confidence": round(self.confidence, 2),
            "influence": self.archetype["influence"],
            "action_count": len(self.action_log),
            "latest_message": self.action_log[-1].get("message", "") if self.action_log else "",
            "latest_action": self.action_log[-1].get("action", "") if self.action_log else "",
        }


# ─── Factory ───────────────────────────────────────────────────────────────
CHINESE_SURNAMES = ["王","李","张","刘","陈","杨","赵","黄","周","吴","徐","孙","马","朱","胡"]
CHINESE_GIVEN    = ["伟","芳","娜","秀英","敏","静","丽","强","磊","洋","艳","勇","峰","桂英","军"]
WESTERN_NAMES    = ["Alex Chen","Sarah Kim","Michael Park","David Zhang","Emma Liu",
                    "James Wu","Oliver Li","Sophia Wang","Lucas Zhao","Isabella Huang"]

def generate_agents(count: int, graph) -> list[Agent]:
    agents = []
    # Distribute archetypes roughly proportionally
    weights = [a["influence"] for a in AGENT_ARCHETYPES]
    total   = sum(weights)
    counts  = [max(1, round(count * w / total)) for w in weights]
    # Trim / pad to exact count
    while sum(counts) > count: counts[counts.index(max(counts))] -= 1
    while sum(counts) < count: counts[counts.index(min(counts))] += 1

    idx = 0
    for archetype, n in zip(AGENT_ARCHETYPES, counts):
        ctx = graph.get_context_for_agent(archetype["type"]) if graph else ""
        for _ in range(n):
            # Pick name
            if random.random() < 0.6:
                name = random.choice(CHINESE_SURNAMES) + random.choice(CHINESE_GIVEN)
            else:
                name = random.choice(WESTERN_NAMES)
            aid = f"agent_{idx:03d}"
            bg  = (f"在{archetype['label']}领域从业{random.randint(3,20)}年，"
                   f"管理资产规模{random.choice(['中等','较大','巨额'])}，"
                   f"风格偏{random.choice(['保守','激进','稳健'])}。")
            agents.append(Agent(aid, archetype, name, bg, ctx))
            idx += 1
    return agents
