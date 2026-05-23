"""
GraphBuilder — GraphRAG-based knowledge graph construction.
Extracts entities and relationships from seed text using LLM,
then builds a NetworkX directed graph for context retrieval.
"""
from __future__ import annotations
import json
import random
import re
from typing import Any

import networkx as nx


# ── Default entities for mock / fallback ──────────────────────────────────────

_FINANCE_ENTITIES = [
    {"id": "e1", "label": "美联储", "type": "org", "description": "美国联邦储备系统，制定货币政策"},
    {"id": "e2", "label": "黄金现货", "type": "price", "description": "国际黄金现货价格，USD/oz"},
    {"id": "e3", "label": "美元指数", "type": "price", "description": "衡量美元对一篮子货币的强弱"},
    {"id": "e4", "label": "通胀预期", "type": "concept", "description": "市场对未来通胀水平的预期"},
    {"id": "e5", "label": "地缘风险", "type": "concept", "description": "地缘政治冲突引发的市场风险溢价"},
    {"id": "e6", "label": "央行购金", "type": "event", "description": "各国央行增持黄金储备的行为"},
    {"id": "e7", "label": "利率决策", "type": "event", "description": "联邦公开市场委员会利率决议"},
    {"id": "e8", "label": "避险情绪", "type": "concept", "description": "市场参与者的风险规避偏好"},
]

_FINANCE_EDGES = [
    {"source": "e1", "target": "e3", "label": "影响", "weight": 0.9},
    {"source": "e1", "target": "e7", "label": "决定", "weight": 0.95},
    {"source": "e3", "target": "e2", "label": "负相关", "weight": 0.85},
    {"source": "e4", "target": "e2", "label": "正相关", "weight": 0.80},
    {"source": "e5", "target": "e8", "label": "推升", "weight": 0.75},
    {"source": "e8", "target": "e2", "label": "带动", "weight": 0.70},
    {"source": "e6", "target": "e2", "label": "支撑", "weight": 0.85},
]

_ROLE_CONTEXT = {
    "央行官员": "关注通胀预期、货币政策信号、利率决策对金融稳定的影响",
    "政策制定者": "关注宏观经济数据、监管框架、系统性风险",
    "机构投资者": "关注黄金现货价格、美元指数、长期资产配置",
    "对冲基金": "关注短期价格动能、杠杆机会、套利策略",
    "地缘分析师": "关注地缘风险、避险情绪、大宗商品供应链",
    "媒体分析师": "关注市场叙事、情绪传导、公众预期",
    "商品交易员": "关注供需平衡、技术支撑位、期货持仓",
    "散户交易者": "关注价格趋势、情绪热点、跟风操作",
}


class GraphBuilder:
    """Builds a knowledge graph from seed text using LLM extraction."""

    def __init__(self, llm):
        self._llm = llm
        self._graph = nx.DiGraph()
        self._nodes: list[dict] = []
        self._edges: list[dict] = []
        self._summary: str = ""

    async def build(self, seed_text: str, goal: str) -> dict:
        """
        Extract entities & relationships from seed_text, build graph.
        Returns dict with 'entities', 'summary', 'stats'.
        """
        prompt = f"""从以下种子文本中提取知识图谱，以JSON格式返回，格式如下：
{{
  "entities": [
    {{"id": "e1", "label": "实体名称", "type": "org|person|concept|event|price", "description": "简短描述"}}
  ],
  "relationships": [
    {{"source": "e1", "target": "e2", "label": "关系描述", "weight": 0.8}}
  ],
  "summary": "对种子文本的简短摘要（2-3句话），聚焦于预测目标"
}}

预测目标：{goal}
种子文本：{seed_text[:2000]}

只返回JSON，不要其他内容。"""

        try:
            resp = await self._llm.chat.completions.create(
                model="mock",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip markdown fences if present
            raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)
            entities = data.get("entities", _FINANCE_ENTITIES)
            relationships = data.get("relationships", _FINANCE_EDGES)
            self._summary = data.get("summary", f"基于种子材料，分析{goal}的关键驱动因素。")
        except Exception:
            # Fallback to default finance graph
            entities = _FINANCE_ENTITIES
            relationships = _FINANCE_EDGES
            self._summary = f"基于种子材料构建知识图谱，聚焦于{goal}的关键驱动因素。"

        # Build NetworkX graph
        for ent in entities:
            self._graph.add_node(ent["id"], **ent)
        for rel in relationships:
            self._graph.add_edge(
                rel["source"], rel["target"],
                label=rel.get("label", "关联"),
                weight=rel.get("weight", 0.5),
            )

        self._nodes = entities
        self._edges = relationships

        return {
            "entities": entities,
            "summary": self._summary,
            "stats": {
                "nodes": len(entities),
                "edges": len(relationships),
            },
        }

    def get_graph_data(self) -> dict:
        """Return graph data for frontend visualization."""
        return {"nodes": self._nodes, "edges": self._edges}

    def get_context_for_agent(self, role: str) -> str:
        """Return relevant graph context for a given agent role."""
        base = _ROLE_CONTEXT.get(role, "关注市场动态和价格信号")
        # Add a few key entities from the graph
        key_nodes = self._nodes[:4] if self._nodes else []
        entities_str = "、".join(n["label"] for n in key_nodes)
        return f"{base}。关键实体：{entities_str}。图谱摘要：{self._summary[:200]}"
