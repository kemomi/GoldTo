"""
CrewAI 工厂 — 定义情报分析 Agent 和 Task
在真实 LLM 模式下调用 CrewAI 编排多 Agent 协作
"""
from __future__ import annotations
from typing import List

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except Exception:
    CREWAI_AVAILABLE = False

from config import settings


# ── 工具定义 ──────────────────────────────────────────────────────────────────

class SearchEventsTool(BaseTool):
    """搜索与主题相关的事件"""
    name: str = "search_events"
    description: str = "搜索与给定主题相关的全球事件和新闻"

    def _run(self, topic: str) -> str:
        # 实际场景中这里会查询数据库或API
        return f"已搜索到关于「{topic}」的近期事件列表（工具返回）"


class MarketDataTool(BaseTool):
    """获取市场数据"""
    name: str = "market_data"
    description: str = "获取相关资产的市场价格、波动率等数据"

    def _run(self, asset: str) -> str:
        return f"{asset} 当前价格：$85.4，24h 波动率 2.3%，成交量放大"


# ── Agent 工厂 ────────────────────────────────────────────────────────────────

def create_agents(llm=None):
    """创建情报分析 Agent 团队"""
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI not available")

    # 使用默认 LLM 配置
    from crewai.llm import LLM
    _llm = llm or LLM(
        model=settings.llm_model_name,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )

    collector = Agent(
        role="全球事件采集员",
        goal="从多渠道收集与分析主题相关的最新事件和信号",
        backstory=(
            "你是一位资深情报分析师，擅长从新闻、社交媒体和官方公告中"
            "筛选关键信号。你关注细节，善于发现容易被忽视但影响深远的事件。"
        ),
        llm=_llm,
        verbose=True,
        tools=[SearchEventsTool()],
    )

    market_analyst = Agent(
        role="金融市场分析师",
        goal="评估事件对全球金融市场和相关资产价格的潜在影响",
        backstory=(
            "你在投行工作了15年，专注于宏观策略。你擅长将地缘政治事件"
            "转化为市场语言，判断资金流向和风险溢价变化。"
        ),
        llm=_llm,
        verbose=True,
        tools=[MarketDataTool()],
    )

    policy_analyst = Agent(
        role="政策与合规分析师",
        goal="分析政策变化、监管动向及其对行业和市场的长期影响",
        backstory=(
            "你曾在监管机构任职，深谙政策制定逻辑。你能从一份草案中"
            "读出未来的合规成本和市场准入门槛变化。"
        ),
        llm=_llm,
        verbose=True,
    )

    briefing_writer = Agent(
        role="情报简报撰写员",
        goal="将所有分析结果整合为结构清晰、 actionable 的情报简报",
        backstory=(
            "你是顶级咨询公司的合伙人，每天为高管撰写决策简报。"
            "你知道决策者最关心什么：风险等级、时间窗口和具体建议。"
        ),
        llm=_llm,
        verbose=True,
    )

    return collector, market_analyst, policy_analyst, briefing_writer


def create_tasks(agents, topic: str, events_text: str) -> List[Task]:
    """为分析主题创建任务链"""
    collector, market_analyst, policy_analyst, briefing_writer = agents

    task_collect = Task(
        description=f"""
基于以下已采集的事件列表，进行初步筛选和分类，提炼出与「{topic}」
最相关的 3-5 个核心事件，并说明每个事件的关键信号和潜在连锁反应。

事件列表：
{events_text}
""",
        expected_output="核心事件清单（含信号解读和连锁反应预测）",
        agent=collector,
    )

    task_market = Task(
        description=f"""
基于采集员筛选的核心事件，分析其对金融市场和相关资产的短期（1-7天）
和中期（1-3个月）影响。评估以下维度：
- 资产价格波动方向和大致幅度
- 波动率变化预期
- 资金流向推测
- 历史类似事件的对比

分析主题：{topic}
""",
        expected_output="市场影响评估报告（含短期和中期预判）",
        agent=market_analyst,
    )

    task_policy = Task(
        description=f"""
分析「{topic}」涉及的政策和监管层面的潜在变化：
- 现有政策是否可能调整
- 新的监管工具是否可能出台
- 对跨境贸易、投资、数据流动的影响
- 各国政策协调或冲突的可能性
""",
        expected_output="政策影响分析报告",
        agent=policy_analyst,
    )

    task_briefing = Task(
        description=f"""
综合采集员、市场分析师和政策分析师的输出，撰写一份面向决策者的高管简报。
简报要求：
- 标题醒目
- 核心摘要不超过150字
- 关键发现分点列出
- 风险评估用红绿灯标识（高/中/低）
- 给出3条具体、可执行的建议
- 标注信息置信度

主题：{topic}
""",
        expected_output="结构化情报简报（Markdown格式）",
        agent=briefing_writer,
    )

    return [task_collect, task_market, task_policy, task_briefing]


def create_crew(agents, tasks) -> Crew:
    """创建 Crew 编排器"""
    return Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )


# ── Mock 简报生成（MVP / 无 LLM Key 时使用） ─────────────────────────────────

def generate_mock_briefing(topic: str, events: list, agents: list, sources_reference: list = None) -> str:
    """
    当没有真实 LLM 时，生成模拟的 Markdown 简报。
    被 daily_briefing_job 和 analysis_engine 共用。
    """
    def _event_sources_md(event):
        refs = event.get('sources_reference', [])
        if not refs:
            return ""
        ref_links = " / ".join([f"[{r['name']}]({r['url']})" for r in refs[:3]])
        return f"<br>📎 来源参考：{ref_links}"

    events_md = "\n".join([
        f"- **{e.get('title', '未命名事件')}**（{e.get('source', '未知来源')}）：{e.get('summary', '')[:80]}...{_event_sources_md(e)}"
        for e in events[:5]
    ]) if events else "- 今日未监测到显著事件"

    agents_md = "\n\n".join([
        f"### {a.get('name', '分析师')} — {a.get('role', '')}\n{a.get('insight', '')}"
        for a in agents
    ]) if agents else "### 情报分析师\n今日数据不足以形成深度分析。"

    # 信息来源参考
    sources_md = ""
    if sources_reference:
        sources_lines = []
        for src in sources_reference:
            cat_name = {
                "geopolitics": "地缘政治", "market": "市场动态", "policy": "政策监管",
                "competitor": "竞争对手", "social": "社交媒体", "product": "产品趋势",
                "legal": "法律合规", "tech": "科技创新", "energy": "能源",
            }.get(src.get("category"), src.get("category", "综合"))
            refs = src.get("references", [])
            if refs:
                ref_lines = "\n".join([f"  - [{r['name']}]({r['url']}) — {r['desc']}" for r in refs[:5]])
                sources_lines.append(f"### {cat_name}\n{ref_lines}")
        if sources_lines:
            sources_md = "\n\n".join(sources_lines)

    sources_section = f"\n\n## 📎 信息来源参考\n\n以下为本简报各板块的主要信息来源，供查验信息真伪时参考：\n\n{sources_md}\n" if sources_md else ""

    return f"""# 🎯 情报简报：{topic}

## 核心摘要
整体风险等级为 **中等偏高**，建议在未来 48-72 小时内密切监控事态发展。

## 📡 关键事件监测
{events_md}

## 🔍 多维度分析
{agents_md}

## ⚠️ 风险评估
| 维度 | 评级 | 说明 |
|------|------|------|
| 市场波动 | 🔴 高风险 | 波动率已上升，资金流向避险资产 |
| 政策影响 | 🟡 中等风险 | 潜在监管变化，窗口期约2周 |
| 地缘连锁 | 🟡 中等风险 | 区域影响可控，需防外溢 |
| 信息置信度 | 🟢 较高 | 基于公开数据源，交叉验证充分 |

## 💡 决策建议
1. **短期（24-48h）**：降低风险敞口，增加现金或避险资产配置
2. **中期（1-2周）**：关注政策细则出台，评估合规成本变化
3. **长期（1-3月）**：若事态缓和，可逢低布局被错杀资产
{sources_section}
---
*Generated by GoldTo Intelligence Engine | Mock Mode*
"""
