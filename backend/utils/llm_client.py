"""OpenAI-compatible LLM client using requests (no openai package needed)."""
import json, os, requests, time
from typing import Optional

class LLMClient:
    def __init__(self):
        self.api_key   = os.environ.get("LLM_API_KEY", "")
        self.base_url  = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model     = os.environ.get("LLM_MODEL_NAME", "qwen-plus")
        self.timeout   = 60
        _PLACEHOLDERS = {"your_api_key_here", "your_api_key", "sk-xxx", "placeholder", ""}
        self._mock     = not bool(self.api_key) or self.api_key.lower() in _PLACEHOLDERS or \
                         self.api_key.startswith("your_")

    # ─── public ────────────────────────────────────────────────────────────
    def chat(self, messages: list[dict], system: str = "", temperature: float = 0.8,
             max_tokens: int = 800) -> str:
        if self._mock:
            return self._mock_response(messages)
        payload = {
            "model": self.model,
            "messages": self._build_messages(messages, system),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        for attempt in range(3):
            try:
                resp = requests.post(
                    f"{self.base_url.rstrip('/')}/chat/completions",
                    headers=headers, json=payload, timeout=self.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                if attempt == 2:
                    return f"[LLM Error: {e}]"
                time.sleep(2 ** attempt)
        return ""

    def json_chat(self, messages: list[dict], system: str = "", **kw) -> dict:
        raw = self.chat(messages, system=system, **kw)
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw}

    # ─── private ───────────────────────────────────────────────────────────
    def _build_messages(self, messages, system):
        result = []
        if system:
            result.append({"role": "system", "content": system})
        result.extend(messages)
        return result

    def _mock_response(self, messages: list[dict]) -> str:
        """Differentiated mock responses for demo / no-key mode."""
        import random as _rnd
        last = messages[-1]["content"] if messages else ""
        system_msg = messages[0]["content"] if messages and messages[0].get("role") == "system" else ""
        h = hash(last) % 10000

        # ── Knowledge graph extraction ──────────────────────────────────
        if "entities" in last and "relations" in last and "type" in last:
            entities = [
                {"id":"e1","label":"美联储","type":"org","description":"美国中央银行，货币政策制定者"},
                {"id":"e2","label":"黄金","type":"concept","description":"贵金属，避险资产标的"},
                {"id":"e3","label":"美元指数","type":"concept","description":"衡量美元相对强弱的指标"},
                {"id":"e4","label":"通货膨胀","type":"concept","description":"物价持续上涨的经济现象"},
                {"id":"e5","label":"央行购金","type":"event","description":"全球央行增持黄金储备行为"},
                {"id":"e6","label":"地缘政治","type":"concept","description":"国际政治地理格局风险"},
                {"id":"e7","label":"避险情绪","type":"concept","description":"投资者风险厌恶情绪"},
                {"id":"e8","label":"利率政策","type":"concept","description":"货币政策核心工具"},
            ]
            relations = [
                {"source":"e1","target":"e3","label":"影响","weight":0.9},
                {"source":"e1","target":"e8","label":"制定","weight":1.0},
                {"source":"e8","target":"e2","label":"负相关","weight":0.85},
                {"source":"e4","target":"e2","label":"推动需求","weight":0.8},
                {"source":"e5","target":"e2","label":"支撑价格","weight":0.75},
                {"source":"e6","target":"e7","label":"引发","weight":0.7},
                {"source":"e7","target":"e2","label":"推高","weight":0.8},
                {"source":"e3","target":"e2","label":"负相关","weight":0.85},
            ]
            import json as _j
            return _j.dumps({"entities": entities, "relations": relations}, ensure_ascii=False)

        # ── World events generation ──────────────────────────────────────
        if "时序世界事件" in last or ("事件" in last and "JSON数组" in last):
            import re as _re
            n_match = _re.search(r"生成(\d+)个", last)
            n = int(n_match.group(1)) if n_match else 8
            event_pool = [
                "美联储官员发表鹰派讲话，市场加息预期升温，金价承压回调1.2%",
                "中东地缘冲突升级，原油供应受威胁，黄金避险需求骤增",
                "美国CPI数据超预期，通胀顽固性引发黄金对冲买盘涌入",
                "全球央行第三季度净购金量达158吨，创近年单季新高",
                "美元指数跌破100关键支撑，非美资产全面受益，黄金上涨2.1%",
                "IMF下调全球经济增长预期至2.8%，衰退担忧加剧避险配置",
                "科技板块大幅回调，资金向黄金等实物资产轮动迹象明显",
                "美联储会议纪要显示内部分歧加大，政策前景不确定性推高金价",
                "多国央行官员发言支持黄金储备多元化，长期需求预期改善",
                "美债收益率曲线倒挂加深，市场衰退信号推动黄金配置需求",
                "对冲基金CFTC持仓报告显示黄金净多头大幅增加至年内高位",
                "黄金ETF持仓周环比增加23吨，散户与机构共振买入",
            ]
            selected = []
            for i in range(n):
                selected.append(event_pool[i % len(event_pool)])
            import json as _j
            return _j.dumps(selected, ensure_ascii=False)

        # ── Agent reaction (JSON format) ─────────────────────────────────
        if "sentiment" in last and "看涨|看跌|中性" in last:
            sentiments = ["看涨", "看涨", "看跌", "中性", "看涨", "看跌"]
            actions_bull = [
                "加仓黄金ETF持仓，同时买入看涨期权以对冲尾部风险",
                "向机构客户发送黄金增配建议报告，预测6周内上涨5-8%",
                "协调多家央行讨论黄金储备占比提升议题",
                "推出黄金主题投资产品，社交媒体放大看涨叙事",
            ]
            actions_bear = [
                "逐步减持黄金仓位，等待更好入场点位",
                "发布风险提示报告，警告市场过热信号",
                "暂缓黄金相关政策讨论，等待更多数据",
            ]
            actions_neut = [
                "维持现有仓位不变，密切跟踪美联储表态",
                "对黄金走势保持中性看法，均衡配置",
                "收集更多市场信息后再做决策",
            ]
            sent = sentiments[h % len(sentiments)]
            if sent == "看涨":
                action = actions_bull[h % len(actions_bull)]
                msg_pool = [
                    "当前利率环境对黄金利好，机构正在悄悄布局，建议跟进。",
                    "地缘风险持续，黄金作为终极避险资产价值凸显，我已加仓。",
                    "从技术面看，黄金突破关键阻力位，上行空间打开。",
                ]
            elif sent == "看跌":
                action = actions_bear[h % len(actions_bear)]
                msg_pool = [
                    "市场情绪过热，获利了结时机已到，需警惕回调风险。",
                    "美元若企稳反弹，将对黄金形成压力，需谨慎操作。",
                    "当前估值偏高，等待回调后再考虑建仓。",
                ]
            else:
                action = actions_neut[h % len(actions_neut)]
                msg_pool = [
                    "多空信号交织，保持观望，等待方向明确后再操作。",
                    "目前市场分歧较大，维持现有配置，关注下一个催化剂。",
                    "均衡配置是当前最优策略，避免单边押注。",
                ]
            msg = msg_pool[h % len(msg_pool)]
            import json as _j
            return _j.dumps({
                "sentiment": sent,
                "action": action,
                "message": msg,
                "influence_score": round(0.4 + (h % 60) / 100, 2)
            }, ensure_ascii=False)

        # ── Full report generation ───────────────────────────────────────
        if "ReportAgent" in system_msg or ("执行摘要" in last and "报告" in last):
            import re as _re
            rounds = _re.search(r"模拟轮次[：:]\s*(\d+)", last)
            agents_n = _re.search(r"参与智能体[：:]\s*(\d+)", last)
            r_n = rounds.group(1) if rounds else "10"
            a_n = agents_n.group(1) if agents_n else "20"
            return (
                f"## 📊 GoldTo 群体智能预测报告\n\n"
                f"### 执行摘要\n"
                f"本次仿真运行 **{r_n} 轮次**，{a_n} 个智能体（机构投资者、散户、央行官员、媒体分析师等）"
                f"在平行数字世界中自由博弈，捕捉群体涌现信号。\n\n"
                f"### 情绪演变路径\n"
                f"- **早期（R1-R3）**：市场对美联储政策存在分歧，情绪以中性为主（占比约45%）\n"
                f"- **中期（R4-R6）**：央行购金消息传导，看涨情绪逐步占优，机构开始布局\n"
                f"- **后期（R7+）**：地缘风险叠加通胀预期，多方共振，看涨阵营扩大至60%以上\n\n"
                f"### 关键涌现行为\n"
                f"- 🔺 **社会传染效应**：机构投资者看涨表态快速传导至散户，形成正反馈\n"
                f"- ⚡ **信息级联**：媒体分析师放大央行购金信号，影响力倍增\n"
                f"- 🌊 **羊群效应激活**：当看涨占比突破55%时，中性智能体快速转向\n\n"
                f"### 预测结论\n"
                f"**核心预测**：基于群体情绪涌现，未来 **6 周黄金价格大概率上涨 4-8%**\n\n"
                f"| 情景 | 概率 | 价格区间 | 驱动因素 |\n"
                f"|------|------|----------|----------|\n"
                f"| 强势上涨 | 35% | +8%~+12% | 美联储转鸽+地缘升级 |\n"
                f"| 温和上涨 | 45% | +3%~+8% | 央行购金持续+通胀韧性 |\n"
                f"| 震荡整理 | 15% | -2%~+3% | 美元反弹压制 |\n"
                f"| 下行风险 | 5% | -5%~-2% | 黑天鹅：快速衰退交易 |\n\n"
                f"### ⚠️ 风险提示\n"
                f"1. 美联储意外鹰派转向可能打压黄金需求\n"
                f"2. 黑天鹅事件（金融危机）导致流动性危机，黄金被动抛售\n"
                f"3. 本预测基于群体智能模拟，不构成投资建议"
            )

        # ── ReportAgent/Agent interactive chat ──────────────────────────
        if "ReportAgent" in system_msg:
            qa_map = {
                "涌现": "本次模拟中最显著的涌现现象是第4轮触发的情绪级联：机构投资者看涨表态后，散户以72%的跟随率迅速转向，媒体分析师进一步放大信号，形成全局看涨共识。这种非线性的集体行为正是群体智能预测的核心价值所在。",
                "风险": "主要风险来自三个维度：①美联储政策超预期鹰派；②全球经济深度衰退引发流动性危机；③大规模加密资产抛售传导至贵金属市场。模型显示这些尾部风险概率约20%。",
                "置信": "本次预测置信度约72%。决定性因素是：智能体情绪共识度（看涨智能体占比>60%持续3轮以上）和涌现行为的方向一致性。若有真实LLM接入，精度将显著提升。",
            }
            for key, ans in qa_map.items():
                if key in last:
                    return ans
            return (
                "从全知视角分析：本次模拟中，15个智能体形成了清晰的三阶段情绪演进——"
                "初期分歧→中期汇聚→后期共识。关键拐点在于央行购金消息触发了机构投资者的"
                "集体行动，随后通过社会传染机制影响散户群体，体现了典型的群体涌现特征。"
                "预测结论：6周内黄金价格看涨概率为80%，核心区间上涨4-8%。"
            )

        # ── Agent persona chat ───────────────────────────────────────────
        if "你扮演" in system_msg or "身份" in system_msg:
            name_match = __import__("re").search(r"你扮演(.{2,8})，", system_msg)
            name = name_match.group(1) if name_match else "我"
            role_match = __import__("re").search(r"一位(.{2,12})。", system_msg)
            role = role_match.group(1) if role_match else "市场参与者"
            responses = [
                f"作为{name}（{role}），我的判断是：当前市场存在明显的结构性做多机会。"
                f"地缘风险和通胀韧性构成双重支撑，机构资金已开始悄然布局。"
                f"我建议在价格回调时分批建仓，目标位上移8-10%。",
                f"我（{name}）持谨慎乐观态度。{role}的视角告诉我，情绪过热时往往是风险积累的时刻。"
                f"建议等待技术面确认后再追多，止损设在近期低点下方2%。",
                f"({name}·{role}) 从我的专业角度看，当前政策环境对黄金是中性偏多的。"
                f"最大的不确定性来自美联储，一旦转鸽信号明确，将触发新一轮上涨行情。",
            ]
            return responses[h % len(responses)]

        # ── Default fallback ─────────────────────────────────────────────
        pool = [
            "市场信号综合显示：当前黄金处于多空拉锯阶段，建议关注美联储下次会议指引。",
            "从群体智能视角来看，情绪共识尚未形成，需要更多轮次的博弈来收敛预测。",
            "数据显示避险情绪主导当前市场，黄金的配置价值在中长期维度依然突出。",
        ]
        return pool[h % len(pool)]


llm = LLMClient()
