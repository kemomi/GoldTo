"""Swarm simulation engine: runs rounds of agent interaction and tracks emergence."""
import threading, time, json, random, uuid
from dataclasses import dataclass, field
from enum import Enum
from utils.llm_client import llm
from agents.agent import Agent, generate_agents, BULLISH, BEARISH, NEUTRAL

class SimStatus(str, Enum):
    IDLE       = "idle"
    BUILDING   = "building"
    SIMULATING = "simulating"
    DONE       = "done"
    ERROR      = "error"


@dataclass
class RoundResult:
    round_num: int
    world_event: str
    agent_reactions: list[dict]
    sentiment_breakdown: dict
    dominant_sentiment: str
    emergence_signal: str = ""


class Simulation:
    def __init__(self, sim_id: str):
        self.id        = sim_id
        self.status    = SimStatus.IDLE
        self.agents: list[Agent] = []
        self.rounds: list[RoundResult] = []
        self.total_rounds = 0
        self.current_round = 0
        self.prediction_target = ""
        self.seed_text  = ""
        self.graph      = None
        self.report     = ""
        self.error_msg  = ""
        self.progress   = 0          # 0-100
        self._lock      = threading.Lock()
        self._thread: threading.Thread | None = None

    # ─── public API ────────────────────────────────────────────────────────
    def start(self, seed_text: str, prediction_target: str,
              agent_count: int = 20, num_rounds: int = 10):
        self.seed_text         = seed_text
        self.prediction_target = prediction_target
        self.total_rounds      = num_rounds
        self.agent_count_req   = agent_count
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def get_state(self) -> dict:
        with self._lock:
            return {
                "id":               self.id,
                "status":           self.status.value,
                "progress":         self.progress,
                "current_round":    self.current_round,
                "total_rounds":     self.total_rounds,
                "agent_count":      len(self.agents),
                "prediction_target":self.prediction_target,
                "rounds":           [self._round_to_dict(r) for r in self.rounds[-5:]],
                "report":           self.report,
                "error":            self.error_msg,
                "sentiment_trend":  self._sentiment_trend(),
            }

    def get_agents(self) -> list[dict]:
        return [a.to_dict() for a in self.agents]

    def chat_with_agent(self, agent_id: str, message: str) -> str:
        agent = next((a for a in self.agents if a.id == agent_id), None)
        if not agent:
            return "找不到该智能体"
        context = f"当前模拟主题：{self.prediction_target}\n最新世界事件：{self._latest_event()}"
        return agent.chat(message, context)

    def chat_with_report_agent(self, message: str) -> str:
        """ReportAgent that has access to all simulation data."""
        system = (
            "你是GoldTo系统的ReportAgent，你拥有对整个模拟世界的全知视角。\n"
            "你可以分析智能体行为、情绪演变、涌现现象，并给出专业预测报告。\n"
            "回答详细、专业、有见地，中文回答。"
        )
        context = json.dumps({
            "prediction_target": self.prediction_target,
            "total_rounds": self.total_rounds,
            "agent_count": len(self.agents),
            "sentiment_trend": self._sentiment_trend(),
            "report_summary": self.report[:1000] if self.report else "报告生成中",
        }, ensure_ascii=False)
        msgs = [{"role": "user", "content":
                 f"模拟数据摘要：\n{context}\n\n用户问题：{message}"}]
        return llm.chat(msgs, system=system, temperature=0.7, max_tokens=1000)

    # ─── internal pipeline ─────────────────────────────────────────────────
    def _run(self):
        try:
            # Phase 1: Build knowledge graph
            self._set_status(SimStatus.BUILDING, 5)
            from graph.knowledge_graph import KnowledgeGraph
            self.graph = KnowledgeGraph()
            self.graph.build_from_text(self.seed_text)
            self._set_progress(20)

            # Phase 2: Generate agents
            self.agents = generate_agents(self.agent_count_req, self.graph)
            self._set_progress(35)

            # Phase 3: Generate world events (one per round)
            world_events = self._generate_world_events(self.total_rounds)
            self._set_progress(45)

            # Phase 4: Simulate rounds
            self._set_status(SimStatus.SIMULATING, 45)
            for rnum in range(1, self.total_rounds + 1):
                self.current_round = rnum
                event = world_events[rnum - 1]
                result = self._simulate_round(rnum, event)
                with self._lock:
                    self.rounds.append(result)
                progress = 45 + int(50 * rnum / self.total_rounds)
                self._set_progress(progress)
                time.sleep(0.05)   # allow state reads

            # Phase 5: Generate report
            self._set_progress(96)
            self.report = self._generate_report()
            self._set_status(SimStatus.DONE, 100)

        except Exception as e:
            with self._lock:
                self.status    = SimStatus.ERROR
                self.error_msg = str(e)

    def _simulate_round(self, rnum: int, event: str) -> RoundResult:
        """Run one simulation round for all agents."""
        # Collect peer sentiments from previous round
        peer_sentiments = [a.sentiment for a in random.sample(
            self.agents, min(5, len(self.agents)))]

        reactions = []
        # For efficiency, only call LLM for a sample of agents each round
        active_sample = random.sample(self.agents, min(8, len(self.agents)))
        for agent in active_sample:
            try:
                r = agent.perceive_and_react(event, rnum, peer_sentiments)
                r["agent_id"]   = agent.id
                r["agent_name"] = agent.name
                r["agent_type"] = agent.archetype["label"]
                reactions.append(r)
            except Exception:
                pass

        # Propagate sentiment to non-sampled agents (social contagion)
        for agent in self.agents:
            if agent not in active_sample:
                influential = max(active_sample, key=lambda a: a.archetype["influence"],
                                  default=None)
                if influential and random.random() < influential.archetype["influence"] * 0.3:
                    agent.sentiment = influential.sentiment

        breakdown   = self._sentiment_breakdown()
        dominant    = max(breakdown, key=breakdown.get)
        emergence   = self._detect_emergence(rnum, breakdown)
        return RoundResult(rnum, event, reactions, breakdown, dominant, emergence)

    def _generate_world_events(self, n: int) -> list[str]:
        prompt = (
            f"请为以下预测主题生成{n}个连续的时序世界事件（每个15-30字，按时间顺序）。\n"
            f"预测主题：{self.prediction_target}\n"
            f"背景材料关键词：{self.seed_text[:500]}\n\n"
            f"只返回JSON数组：[\"事件1\",\"事件2\",...]，不要其他内容。"
        )
        result = llm.json_chat([{"role": "user", "content": prompt}])
        if isinstance(result, list) and len(result) >= n:
            return result[:n]
        if isinstance(result, dict) and "raw" in result:
            # Try to parse the raw string as list
            import re
            items = re.findall(r'"([^"]{10,80})"', result["raw"])
            if len(items) >= n:
                return items[:n]
        # Fallback events
        return self._fallback_events(n)

    def _fallback_events(self, n: int) -> list[str]:
        base = [
            "美联储发表鹰派讲话，市场预期加息概率上升至75%",
            "中东地区局势升温，原油供应受威胁，避险情绪飙升",
            "美国通胀数据超预期，黄金作为抗通胀工具受追捧",
            "全球央行集体增持黄金储备，月度净买入创历史新高",
            "美元指数大幅走弱，非美资产全面上涨",
            "国际货币基金组织下调全球经济增长预期",
            "主要经济体PMI数据不及预期，衰退担忧加剧",
            "科技股大跌引发资金向黄金等避险资产转移",
            "俄乌冲突出现新进展，地缘风险溢价重估",
            "美国财政部发行大量国债，美债收益率攀升",
            "多家大型对冲基金披露增持黄金期货仓位",
            "中国央行连续第12个月增持黄金储备",
        ]
        result = []
        for i in range(n):
            result.append(base[i % len(base)])
        return result

    # ─── emergence detection ───────────────────────────────────────────────
    def _detect_emergence(self, rnum: int, breakdown: dict) -> str:
        bullish_pct = breakdown.get(BULLISH, 0)
        bearish_pct = breakdown.get(BEARISH, 0)
        if rnum > 2 and len(self.rounds) >= 2:
            prev = self.rounds[-1].sentiment_breakdown
            prev_bull = prev.get(BULLISH, 0)
            delta = bullish_pct - prev_bull
            if delta > 20:
                return "🔺 涌现：群体情绪急剧转向看涨，从众效应激活"
            if delta < -20:
                return "🔻 涌现：恐慌蔓延，抛售情绪快速传导"
        if bullish_pct > 75:
            return "⚡ 涌现：市场高度共识看涨，可能出现过热信号"
        if bearish_pct > 75:
            return "❄️ 涌现：悲观情绪主导，市场底部临近？"
        return ""

    # ─── report generation ─────────────────────────────────────────────────
    def _generate_report(self) -> str:
        trend  = self._sentiment_trend()
        sample = [r for r in self.rounds if r.emergence_signal][:3]
        emergence_text = "\n".join(f"- R{r.round_num}: {r.emergence_signal}" for r in sample)
        dominant_final = self.rounds[-1].dominant_sentiment if self.rounds else NEUTRAL

        prompt = (
            f"你是GoldTo预测引擎的ReportAgent。请生成一份专业的预测分析报告（Markdown格式）。\n\n"
            f"## 模拟参数\n"
            f"- 预测目标：{self.prediction_target}\n"
            f"- 模拟轮次：{self.total_rounds}\n"
            f"- 参与智能体：{len(self.agents)}个\n"
            f"- 情绪演变趋势：{json.dumps(trend, ensure_ascii=False)}\n"
            f"- 最终主导情绪：{dominant_final}\n"
            f"- 涌现事件：\n{emergence_text or '无显著涌现'}\n\n"
            f"请生成包含以下部分的完整报告：\n"
            f"1. 执行摘要\n2. 情绪演变分析\n3. 关键涌现行为\n"
            f"4. 预测结论（含数值区间）\n5. 风险提示"
        )
        return llm.chat([{"role": "user", "content": prompt}],
                        temperature=0.5, max_tokens=1500)

    # ─── utilities ─────────────────────────────────────────────────────────
    def _sentiment_breakdown(self) -> dict:
        counts = {BULLISH: 0, BEARISH: 0, NEUTRAL: 0}
        for a in self.agents:
            counts[a.sentiment] = counts.get(a.sentiment, 0) + 1
        total = len(self.agents) or 1
        return {k: round(v / total * 100) for k, v in counts.items()}

    def _sentiment_trend(self) -> list[dict]:
        return [{"round": r.round_num, "breakdown": r.sentiment_breakdown,
                 "dominant": r.dominant_sentiment} for r in self.rounds]

    def _latest_event(self) -> str:
        return self.rounds[-1].world_event if self.rounds else "模拟尚未开始"

    def _set_status(self, status: SimStatus, progress: int):
        with self._lock:
            self.status   = status
            self.progress = progress

    def _set_progress(self, p: int):
        with self._lock:
            self.progress = p

    def _round_to_dict(self, r: RoundResult) -> dict:
        return {
            "round": r.round_num,
            "event": r.world_event,
            "reactions": r.agent_reactions[:4],
            "breakdown": r.sentiment_breakdown,
            "dominant": r.dominant_sentiment,
            "emergence": r.emergence_signal,
        }


# ─── Global simulation registry ────────────────────────────────────────────
_sims: dict[str, Simulation] = {}

def create_simulation() -> Simulation:
    sim_id = str(uuid.uuid4())[:8]
    sim = Simulation(sim_id)
    _sims[sim_id] = sim
    return sim

def get_simulation(sim_id: str) -> Simulation | None:
    return _sims.get(sim_id)

def latest_simulation() -> Simulation | None:
    if not _sims:
        return None
    return list(_sims.values())[-1]
