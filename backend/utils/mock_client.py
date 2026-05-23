"""
MockAsyncOpenAI — 完全离线的 LLM 模拟客户端。
当 LLM_API_KEY 未配置时自动启用，提供真实感的仿真数据。
接口与 openai.AsyncOpenAI 完全兼容。
"""
from __future__ import annotations
import json
import random
import re
from dataclasses import dataclass
from typing import Any


# ── 返回值结构（模拟 openai.types.chat） ──────────────────────────────────────

@dataclass
class _Message:
    content: str
    role: str = "assistant"


@dataclass
class _Choice:
    message: _Message
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class _Response:
    choices: list[_Choice]
    model: str = "mock-model"
    usage: dict = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}


class _Completions:
    async def create(self, model: str, messages: list[dict],
                     max_tokens: int = 1000, temperature: float = 0.8,
                     **kwargs) -> _Response:
        content = _MockResponder.respond(messages)
        return _Response(choices=[_Choice(message=_Message(content=content))])


class _Chat:
    def __init__(self):
        self.completions = _Completions()


class MockAsyncOpenAI:
    """Drop-in replacement for openai.AsyncOpenAI with no network calls."""

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs):
        self.chat = _Chat()
        self._mock = True

    # Keep api_key attribute for compatibility
    @property
    def api_key(self) -> str:
        return "mock"


# ── 响应生成逻辑 ──────────────────────────────────────────────────────────────

class _MockResponder:
    """Generates contextually appropriate mock responses."""

    @staticmethod
    def respond(messages: list[dict]) -> str:
        # Combine all message content for analysis
        all_text = " ".join(m.get("content", "") for m in messages)
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            ""
        )
        system = next(
            (m["content"] for m in messages if m.get("role") == "system"),
            ""
        )
        h = hash(last_user) % 10000

        # ── 1. 知识图谱构建 ──────────────────────────────────────────────────
        if "entities" in all_text and "relationships" in all_text and "summary" in all_text:
            return _MockResponder._graph(last_user, h)

        # ── 2. 人设生成 ──────────────────────────────────────────────────────
        if ("人设" in all_text or "persona" in all_text.lower() or
                "agent_1" in all_text or "initial_stance" in all_text):
            return _MockResponder._personas(last_user, h)

        # ── 3. 智能体互动 ────────────────────────────────────────────────────
        if "dialogue" in all_text and "stance_delta" in all_text:
            return _MockResponder._interaction(last_user, system, h)

        # ── 4. 预测报告 ──────────────────────────────────────────────────────
        if ("执行摘要" in all_text or "预测结论" in all_text or
                "仿真发现" in all_text or "ReportAgent" in system):
            return _MockResponder._report(last_user, h)

        # ── 5. 对话问答 ──────────────────────────────────────────────────────
        return _MockResponder._chat(last_user, system, h)

    # ── 知识图谱 ─────────────────────────────────────────────────────────────
    @staticmethod
    def _graph(text: str, h: int) -> str:
        is_oil = any(w in text for w in ["石油", "原油", "油价", "OPEC", "能源"])
        is_gold = any(w in text for w in ["黄金", "金价", "贵金属", "Gold"])
        is_stock = any(w in text for w in ["股市", "A股", "纳指", "股票"])

        if is_oil:
            entities = [
                {"id": "e1", "name": "OPEC+", "type": "organization", "description": "石油输出国组织及盟友", "importance": 0.95},
                {"id": "e2", "name": "原油价格", "type": "commodity", "description": "国际基准原油现货价格", "importance": 0.90},
                {"id": "e3", "name": "美国页岩油", "type": "concept", "description": "美国非常规石油生产", "importance": 0.80},
                {"id": "e4", "name": "地缘政治风险", "type": "concept", "description": "中东及俄乌局势影响", "importance": 0.85},
                {"id": "e5", "name": "美元指数", "type": "indicator", "description": "原油计价货币强弱", "importance": 0.75},
                {"id": "e6", "name": "全球需求", "type": "concept", "description": "工业用油与出行需求", "importance": 0.80},
                {"id": "e7", "name": "美联储", "type": "organization", "description": "货币政策对能源需求影响", "importance": 0.70},
                {"id": "e8", "name": "EIA库存报告", "type": "event", "description": "美国能源信息署周度数据", "importance": 0.65},
            ]
            relationships = [
                {"source": "e1", "target": "e2", "type": "affects", "description": "减产决定推高油价", "weight": 0.90},
                {"source": "e3", "target": "e2", "type": "affects", "description": "产量增加压低油价", "weight": 0.80},
                {"source": "e4", "target": "e2", "type": "causes", "description": "供应中断风险溢价", "weight": 0.85},
                {"source": "e5", "target": "e2", "type": "influences", "description": "美元走强压制油价", "weight": 0.70},
                {"source": "e7", "target": "e5", "type": "affects", "description": "利率政策驱动美元", "weight": 0.80},
                {"source": "e8", "target": "e6", "type": "follows", "description": "库存折射需求强弱", "weight": 0.65},
            ]
            summary = "当前石油市场受OPEC+减产与美国页岩油产量博弈主导，地缘风险提供价格支撑，美联储政策通过美元间接影响油价。"
        elif is_stock:
            entities = [
                {"id": "e1", "name": "美联储", "type": "organization", "description": "美国货币政策制定机构", "importance": 0.95},
                {"id": "e2", "name": "股市指数", "type": "indicator", "description": "标普500/纳斯达克综合指数", "importance": 0.90},
                {"id": "e3", "name": "科技股", "type": "concept", "description": "高估值成长股板块", "importance": 0.85},
                {"id": "e4", "name": "企业盈利", "type": "indicator", "description": "季报EPS增速", "importance": 0.80},
                {"id": "e5", "name": "通货膨胀", "type": "indicator", "description": "CPI/PCE数据", "importance": 0.80},
                {"id": "e6", "name": "流动性", "type": "concept", "description": "市场资金充裕程度", "importance": 0.75},
                {"id": "e7", "name": "AI热潮", "type": "event", "description": "人工智能带动科技估值", "importance": 0.85},
                {"id": "e8", "name": "地缘政治", "type": "concept", "description": "贸易摩擦与冲突影响", "importance": 0.65},
            ]
            relationships = [
                {"source": "e1", "target": "e6", "type": "affects", "description": "加息收紧流动性", "weight": 0.90},
                {"source": "e6", "target": "e2", "type": "affects", "description": "资金充裕推升股市", "weight": 0.85},
                {"source": "e5", "target": "e1", "type": "influences", "description": "通胀决定货币政策", "weight": 0.90},
                {"source": "e7", "target": "e3", "type": "causes", "description": "AI叙事推高科技估值", "weight": 0.85},
                {"source": "e4", "target": "e2", "type": "affects", "description": "盈利兑现驱动股价", "weight": 0.80},
            ]
            summary = "股市走势由美联储货币政策、企业盈利增速和AI技术革命三重逻辑驱动，流动性是核心变量。"
        else:  # 默认黄金
            entities = [
                {"id": "e1", "name": "美联储", "type": "organization", "description": "美国中央银行，货币政策制定者", "importance": 0.95},
                {"id": "e2", "name": "黄金现货", "type": "commodity", "description": "COMEX黄金现货价格", "importance": 0.90},
                {"id": "e3", "name": "美元指数", "type": "indicator", "description": "衡量美元相对强弱", "importance": 0.85},
                {"id": "e4", "name": "通货膨胀", "type": "indicator", "description": "CPI/PCE通胀数据", "importance": 0.80},
                {"id": "e5", "name": "全球央行购金", "type": "event", "description": "各国央行增持黄金储备", "importance": 0.85},
                {"id": "e6", "name": "地缘政治风险", "type": "concept", "description": "中东冲突、俄乌战争避险需求", "importance": 0.80},
                {"id": "e7", "name": "实际利率", "type": "indicator", "description": "名义利率减通胀预期", "importance": 0.85},
                {"id": "e8", "name": "黄金ETF持仓", "type": "indicator", "description": "机构投资者黄金配置变化", "importance": 0.70},
            ]
            relationships = [
                {"source": "e1", "target": "e7", "type": "affects", "description": "加息推高实际利率", "weight": 0.90},
                {"source": "e7", "target": "e2", "type": "affects", "description": "实际利率上升压制金价", "weight": 0.88},
                {"source": "e3", "target": "e2", "type": "influences", "description": "美元走强压低金价", "weight": 0.82},
                {"source": "e4", "target": "e2", "type": "affects", "description": "通胀推动避险需求", "weight": 0.78},
                {"source": "e5", "target": "e2", "type": "affects", "description": "央行购金支撑金价", "weight": 0.85},
                {"source": "e6", "target": "e2", "type": "causes", "description": "地缘风险推高避险溢价", "weight": 0.80},
                {"source": "e8", "target": "e2", "type": "follows", "description": "ETF持仓反映机构情绪", "weight": 0.72},
            ]
            summary = "黄金价格受美联储利率政策、实际利率水平和全球避险情绪三重驱动，央行持续购金构成长期结构性支撑。"

        return json.dumps({
            "entities": entities,
            "relationships": relationships,
            "summary": summary
        }, ensure_ascii=False)

    # ── 人设生成 ─────────────────────────────────────────────────────────────
    @staticmethod
    def _personas(text: str, h: int) -> str:
        n_match = re.search(r"生成\s*(\d+)\s*个", text)
        n = int(n_match.group(1)) if n_match else 12

        is_oil = any(w in text for w in ["石油", "原油", "油价", "能源"])

        base_personas = [
            {"id": "agent_1", "name": "张明辉", "role": "宏观经济分析师",
             "organization": "中国国际金融股份有限公司", "background": "15年大宗商品研究经验，专注美联储政策解读",
             "personality": "理性、数据驱动、偏保守", "expertise": ["宏观经济", "货币政策", "大宗商品"],
             "initial_stance": 0.35, "motivation": "为机构客户提供准确的资产配置建议"},
            {"id": "agent_2", "name": "李珊", "role": "期货交易员",
             "organization": "高盛（香港）", "background": "8年衍生品交易经验，擅长技术分析和短线操作",
             "personality": "果断、风险偏好高、情绪化", "expertise": ["期货衍生品", "技术分析", "量化交易"],
             "initial_stance": -0.25, "motivation": "捕捉短期价格波动获取超额收益"},
            {"id": "agent_3", "name": "王建国", "role": "央行货币政策研究员",
             "organization": "中国人民银行研究局", "background": "20年货币政策研究，参与多项政策制定",
             "personality": "谨慎、全局思维、信息滞后", "expertise": ["货币政策", "汇率机制", "国际储备"],
             "initial_stance": 0.10, "motivation": "维护金融稳定，优化外汇储备结构"},
            {"id": "agent_4", "name": "陈晓华", "role": "地缘政治分析师",
             "organization": "北京大学国际关系学院", "background": "研究中东及俄乌冲突对大宗商品影响",
             "personality": "多角度思维、历史类比、警惕黑天鹅", "expertise": ["地缘政治", "国际关系", "能源安全"],
             "initial_stance": 0.55, "motivation": "揭示地缘风险对市场的深远影响"},
            {"id": "agent_5", "name": "刘天宇", "role": "对冲基金经理",
             "organization": "桥水联合基金（亚太）", "background": "管理50亿美元多资产组合，擅长逆向投资",
             "personality": "逆向思维、独立判断、高杠杆", "expertise": ["资产配置", "风险对冲", "宏观策略"],
             "initial_stance": -0.40, "motivation": "通过逆向布局获取超额回报"},
            {"id": "agent_6", "name": "赵欣怡", "role": "财经媒体记者",
             "organization": "财新传媒", "background": "深度报道大宗商品市场，影响散户情绪",
             "personality": "叙事驱动、放大效应、情绪化", "expertise": ["市场解读", "投资者情绪", "媒体传播"],
             "initial_stance": 0.20, "motivation": "挖掘市场内幕，引导舆论关注"},
            {"id": "agent_7", "name": "周海峰", "role": "私募基金经理",
             "organization": "景林资产", "background": "专注价值投资，长期持有黄金头寸",
             "personality": "长线思维、价值导向、低换手率", "expertise": ["价值投资", "黄金配置", "另类资产"],
             "initial_stance": 0.60, "motivation": "保护资产免受货币贬值侵蚀"},
            {"id": "agent_8", "name": "吴芳", "role": "学术经济学家",
             "organization": "清华大学五道口金融学院", "background": "研究黄金货币属性与通胀关系",
             "personality": "客观、理论框架强、脱离市场节奏", "expertise": ["货币经济学", "通胀理论", "黄金历史"],
             "initial_stance": -0.05, "motivation": "验证经济理论在实际市场中的预测效力"},
            {"id": "agent_9", "name": "孙磊", "role": "大宗商品交易商",
             "organization": "嘉能可（中国）", "background": "实物黄金贸易15年，掌握供需一手数据",
             "personality": "供需敏感、短视、价差套利", "expertise": ["实物贸易", "供应链", "仓储物流"],
             "initial_stance": 0.15, "motivation": "把握实物供需错配获取贸易利润"},
            {"id": "agent_10", "name": "徐倩", "role": "风险管理师",
             "organization": "中国平安资产管理", "background": "负责保险资金大类资产配置风险控制",
             "personality": "风险厌恶、合规优先、保守稳健", "expertise": ["风险评估", "资产负债管理", "监管合规"],
             "initial_stance": -0.20, "motivation": "控制组合下行风险，确保偿付能力"},
            {"id": "agent_11", "name": "马志远", "role": "散户投资者代表",
             "organization": "个人投资者", "background": "投资黄金5年，主要通过黄金ETF和积存金",
             "personality": "情绪化、跟风、恐惧/贪婪驱动", "expertise": ["技术图表", "社交媒体情绪"],
             "initial_stance": 0.45, "motivation": "通过黄金投资实现资产保值增值"},
            {"id": "agent_12", "name": "钱博文", "role": "国际投行策略师",
             "organization": "摩根士丹利", "background": "全球大宗商品策略负责人，发布有影响力的研究报告",
             "personality": "权威感强、影响市场预期、数据导向", "expertise": ["全球资产配置", "研究报告", "投资者沟通"],
             "initial_stance": 0.30, "motivation": "发布准确预测维护机构声誉"},
        ]

        if is_oil:
            for p in base_personas:
                p["role"] = p["role"].replace("黄金", "石油")
                p["expertise"] = [e.replace("黄金", "能源") for e in p["expertise"]]

        result = base_personas[:n]
        # Pad if needed
        while len(result) < n:
            i = len(result) + 1
            result.append({
                "id": f"agent_{i}", "name": f"参与者{i}", "role": "市场分析师",
                "organization": "金融机构", "background": "市场从业多年",
                "personality": "理性客观", "expertise": ["市场分析"],
                "initial_stance": round(random.uniform(-0.3, 0.3), 2),
                "motivation": "准确判断市场走势"
            })

        return json.dumps(result[:n], ensure_ascii=False)

    # ── 智能体互动 ───────────────────────────────────────────────────────────
    @staticmethod
    def _interaction(text: str, system: str, h: int) -> str:
        # Extract names from prompt
        name_a_match = re.search(r"姓名[：:]\s*(.{2,6})", text)
        name_b_match = re.search(r"你与\s*(.{2,8})\s*[（(]", text)
        name_a = name_a_match.group(1).strip() if name_a_match else "分析师"
        name_b = name_b_match.group(1).strip() if name_b_match else "交易员"

        round_match = re.search(r"回合\s*(\d+)", text)
        round_num = int(round_match.group(1)) if round_match else 1

        stance_match = re.search(r"当前立场[（(]-1.*?[）)][：:]\s*([+-]?\d+\.\d+)", text)
        cur_stance = float(stance_match.group(1)) if stance_match else 0.0

        # Vary dialogues based on round and hash
        dialogue_sets = [
            [
                {"speaker": name_a, "text": f"从我的角度看，当前市场情绪已经过度悲观，基本面并不支持这种预期。政策面的支撑还没有完全被定价。"},
                {"speaker": name_b, "text": f"你说得有道理，但我更关注短期流动性问题。资金面的压力在接下来两周内会是主要矛盾。"},
                {"speaker": name_a, "text": f"流动性问题是暂时的。如果从更长的时间维度来看，结构性需求没有改变。我倾向于在这个位置逐步建仓。"},
                {"speaker": name_b, "text": f"我理解你的逻辑，但我的风控要求我先看到确认信号再加仓。目前我维持中性，不追高也不减仓。"},
            ],
            [
                {"speaker": name_a, "text": f"最新的数据点让我更坚定了看多的判断——机构资金持续流入，这不是散户行为。"},
                {"speaker": name_b, "text": f"机构也会犯错，2008年就是例子。我注意到历史上类似节点往往是陷阱，需要更多验证。"},
                {"speaker": name_a, "text": f"这次的宏观背景和2008年不同，央行的政策工具箱比那时更充足。我认为风险是不对称的——上行空间大于下行。"},
                {"speaker": name_b, "text": f"你改变了我的一些看法。也许我对下行风险过于保守了，可以适当提高多头敞口。"},
            ],
            [
                {"speaker": name_a, "text": f"我需要直接告诉你我的判断：现在的价格已经反映了过多的乐观预期，回调风险被严重低估。"},
                {"speaker": name_b, "text": f"有意思的观点。不过你是否考虑到，市场的一致预期本身就会自我强化？动量因子在短期内不可忽视。"},
                {"speaker": name_a, "text": f"短期动量我承认，但我的模型显示当前估值分位数已经处于历史90%以上，均值回归是大概率事件。"},
                {"speaker": name_b, "text": f"均值回归是会发生，但时间是不确定的。我选择尊重趋势，同时做好对冲，等待反转信号出现。"},
            ],
        ]

        dialogue = dialogue_sets[h % len(dialogue_sets)]
        stance_deltas = [0.08, -0.05, 0.12, -0.10, 0.03, -0.08, 0.15, -0.03]
        delta = stance_deltas[(h + round_num) % len(stance_deltas)]

        insights = [
            f"通过与{name_b}的交流，我意识到短期流动性压力确实不容忽视，但中长期基本面逻辑依然成立。",
            f"这次对话让我认识到，{name_b}对风险的量化方式与我不同，他的历史回测提供了有价值的参考视角。",
            f"与{name_b}交流后，我对市场分歧的深度有了更清晰的认知。这种分歧本身就是机会所在。",
            f"我的核心判断没有改变，但{name_b}的观点提醒我需要在仓位管理上更加谨慎，留出安全垫。",
            f"通过这次交流，我更新了对{name_b}所代表机构立场的判断，这对于预测市场合力方向很有价值。",
        ]
        actions = [
            "将继续持有现有仓位，密切跟踪下周的关键数据窗口。",
            "小幅调整敞口，从偏多转向更均衡的风险配置。",
            "基于交流获得的新信息，向团队汇报并讨论是否调整策略。",
            "将对话内容纳入情景分析框架，更新概率权重。",
            "维持判断，但设置严格的止损线以控制尾部风险。",
        ]

        return json.dumps({
            "dialogue": dialogue,
            "my_insight": insights[h % len(insights)],
            "stance_delta": delta,
            "action": actions[h % len(actions)],
        }, ensure_ascii=False)

    # ── 预测报告 ─────────────────────────────────────────────────────────────
    @staticmethod
    def _report(text: str, h: int) -> str:
        # Extract key numbers from context
        agents_match = re.search(r"智能体数量[：:]\s*(\d+)", text)
        rounds_match = re.search(r"仿真轮次[：:]\s*(\d+)", text)
        interactions_match = re.search(r"总互动次数[：:]\s*(\d+)", text)
        avg_match = re.search(r"平均立场[：:]\s*([+-]?\d+\.\d+)", text)

        n_agents = agents_match.group(1) if agents_match else "12"
        n_rounds = rounds_match.group(1) if rounds_match else "30"
        n_interactions = interactions_match.group(1) if interactions_match else "120"
        avg_stance = float(avg_match.group(1)) if avg_match else 0.18

        is_oil = any(w in text for w in ["石油", "原油", "油价"])
        is_stock = any(w in text for w in ["股市", "A股", "股票"])

        if avg_stance > 0.1:
            direction = "看涨"
            confidence = f"{int(60 + avg_stance * 30)}%"
            range_short = "+4%~+9%"
            range_long = "+8%~+15%"
            bear_scenario = "美联储意外大幅加息"
            bull_scenario = "地缘风险骤升推动避险需求"
        elif avg_stance < -0.1:
            direction = "看跌"
            confidence = f"{int(60 + abs(avg_stance) * 25)}%"
            range_short = "-3%~-8%"
            range_long = "-6%~-12%"
            bear_scenario = "基本面超预期恶化"
            bull_scenario = "政策超预期宽松刺激"
        else:
            direction = "震荡"
            confidence = "58%"
            range_short = "-2%~+4%"
            range_long = "-4%~+7%"
            bear_scenario = "宏观数据持续不及预期"
            bull_scenario = "风险偏好改善资金回流"

        asset = "石油" if is_oil else ("股市" if is_stock else "黄金")

        return f"""## 📊 GoldTo 群体智能预测报告

### 执行摘要

本次仿真历时 **{n_rounds} 轮**，{n_agents} 个具有独立人格与记忆的智能体（机构投资者、交易员、政策研究员、媒体记者、学术专家等）在数字平行世界中展开 **{n_interactions} 次深度博弈**。

通过捕捉群体互动产生的涌现信号，模型综合判断：**{asset}价格短期内大概率呈{direction}趋势**，置信度 **{confidence}**。

---

## 仿真发现

### 群体立场演化

仿真过程中，智能体立场呈现清晰的三阶段演化：

- **初期（R1~R{int(int(n_rounds)*0.3)}）**：市场存在明显分歧，多空阵营各执一词，平均立场接近中性
- **中期（R{int(int(n_rounds)*0.3)+1}~R{int(int(n_rounds)*0.7)}）**：信息级联效应显现，{direction}阵营逐步扩大，关键意见领袖发挥放大效应
- **后期（R{int(int(n_rounds)*0.7)+1}~R{n_rounds}）**：群体共识基本形成，{direction}预期主导市场叙事

### 关键分歧点

1. **时间维度分歧**：短线交易者关注流动性窗口，长线投资者聚焦结构性需求，形成持续张力
2. **风险定价分歧**：部分智能体对尾部风险估计不足（过度乐观），风险管理者持续提供反向约束
3. **信息解读分歧**：相同数据（如央行政策信号）在不同角色间产生截然不同的解读，引发多轮辩论

### 涌现趋势

- 🔺 **信息级联**：机构分析师的判断通过媒体记者快速扩散，放大效应显著
- 🌊 **羊群效应**：当{direction}阵营超过55%时，中性智能体加速转向
- ⚡ **反身性循环**：预期变化本身影响行为，行为验证预期，形成自我强化

---

## 预测结论

| 维度 | 详情 |
|------|------|
| **主预测方向** | {direction} |
| **置信度** | {confidence} |
| **短期区间（1-4周）** | {range_short} |
| **中期区间（1-3月）** | {range_long} |
| **关键催化剂** | {bull_scenario} |

**情景概率分布：**

| 情景 | 概率 | 说明 |
|------|------|------|
| 强势{direction} | 25% | 多重利好共振 |
| 温和{direction} | 45% | 基准情景 |
| 震荡 | 20% | 多空势均力敌 |
| 反向运动 | 10% | 黑天鹅触发 |

---

## 风险因素

### 上行风险
- {bull_scenario}导致价格加速上行
- 机构资金集中流入形成正反馈
- 技术面突破关键阻力触发程序化买盘

### 下行风险
- {bear_scenario}打压市场情绪
- 流动性危机导致被动平仓
- 监管政策超预期收紧

---

## 核心驱动力

1. **宏观货币政策**：美联储利率路径仍是最大变量，每次讲话都可能重新定价
2. **实物需求支撑**：结构性需求提供价格底部，不轻易被情绪主导
3. **群体预期管理**：市场预期本身具有自我实现特性，需关注共识转变节点

---

## 操作建议

> ⚠️ 以下建议基于群体智能仿真，不构成投资建议，请结合个人风险偏好决策。

- **激进型**：分批建立{direction}方向仓位，目标{range_short}，止损设于入场价-3%
- **稳健型**：等待价格确认信号后入场，仓位控制在总资产15%以内
- **保守型**：持仓观望，关注关键数据窗口，避免追涨杀跌

---

*本报告由 GoldTo 群体智能引擎自动生成 · Mock 模式 · 仅供演示*"""

    # ── 对话问答 ────────────────────────────────────────────────────────────
    @staticmethod
    def _chat(text: str, system: str, h: int) -> str:
        is_agent_chat = "你正在扮演" in system or "完全沉浸在角色" in system
        is_report_chat = "ReportAgent" in system or "报告智能体" in system

        if is_agent_chat:
            name_match = re.search(r"姓名[：:]\s*(.{2,8})", system)
            role_match = re.search(r"职位[：:]\s*(.{2,20})", system)
            stance_match = re.search(r"当前立场[（(]-1.*?[）)][：:]\s*([+-]?\d+\.\d+)", system)
            name = name_match.group(1).strip() if name_match else "分析师"
            role = role_match.group(1).strip() if role_match else "市场观察者"
            stance = float(stance_match.group(1)) if stance_match else 0.0
            stance_desc = "明显看涨" if stance > 0.3 else ("偏空" if stance < -0.3 else "中性偏多")

            responses = [
                f"作为{name}，我的判断很明确。从{role}的视角来看，当前市场的定价并没有充分反映结构性风险。我的立场是{stance_desc}，这个判断基于我多年的从业经验和当前的基本面数据。你有什么具体的疑问想探讨？",
                f"({name} | {role}) 这是个好问题。我的立场（{stance:+.2f}）形成于对当前宏观环境的综合判断：货币政策走向、资金流向变化、以及我掌握的一些行业内部信息。从我的角度来看，市场共识存在系统性偏差，这正是机会所在。",
                f"我（{name}）对此有明确的观点。{role}这个岗位让我能够接触到普通投资者看不到的信息流。当前的价格走势背后，有几个关键变量被市场低估了。具体来说，我认为接下来的1-2个月将是关键观察窗口。",
            ]
            return responses[h % len(responses)]

        if is_report_chat:
            responses_report = [
                "基于完整的仿真数据分析，这次模拟中最显著的涌现现象发生在中期阶段：机构分析师与政策研究员之间的分歧触发了一次明显的信息级联。当两个高影响力智能体达成共识后，其他11个智能体在3轮内相继调整了立场，体现了经典的羊群效应。这也是我们预测置信度能够达到65%以上的核心依据。",
                "从全知视角来看，这次仿真揭示了一个重要规律：在所有12个智能体中，有3个关键节点（机构分析师、央行研究员、对冲基金经理）的立场变化对最终群体共识的形成贡献了约70%的影响力。这符合复杂系统中的'少数节点主导'理论。建议你重点关注这三个角色的最新洞察。",
                "根据仿真结果，置信度相对较高（约65%）。这个数值来自两个维度的综合评估：①群体立场收敛的速度（快速收敛通常意味着信号更强）；②互动过程中的分歧强度（高质量的多空辩论产生更有效的价格发现）。如果你想了解某个具体风险情景的概率，可以告诉我。",
            ]
            return responses_report[h % len(responses_report)]

        # Generic responses
        generic = [
            "基于本次群体智能仿真的完整分析，市场的核心矛盾正在从流动性驱动转向基本面驱动。这个转变点通常是最佳的策略切换时机。你具体想了解哪个维度？",
            "这是一个好问题。从多智能体系统的视角来看，当前市场处于预期重建阶段。历史数据显示，这个阶段往往伴随着较高的波动率，但也孕育着最大的机会。",
            "仿真结果显示，影响最终走势的关键变量按重要性排序：①政策信号（权重35%）②资金流向（权重28%）③供需基本面（权重22%）④情绪指标（权重15%）。你最关心哪个维度的分析？",
        ]
        return generic[h % len(generic)]
