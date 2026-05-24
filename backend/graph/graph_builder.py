"""
GraphRAG Builder
Step 1 of pipeline: extract entities & relationships from seed document,
build a NetworkX knowledge graph, and provide context retrieval.
"""
from __future__ import annotations
import json
import re
from typing import Any
import networkx as nx
from openai import AsyncOpenAI
from config import settings

_ENTITY_PROMPT = """
你是周大福海外市场战略情报系统的知识图谱构建专家。请从以下文本中提取关键实体和关系，用于海外市场情报分析。

文本：
{text}

情报任务：{goal}

请提取：
- entities: 关键实体（市场/国家、城市、品牌、竞品、产品系列、渠道、平台、政策、风险、指标等）
- relationships: 实体之间的关系

严格返回 JSON，格式如下（不要有任何其他内容）：
{{
  "entities": [
    {{"id": "e1", "name": "...", "type": "...", "description": "...", "importance": 0.8}}
  ],
  "relationships": [
    {{"source": "e1", "target": "e2", "type": "...", "description": "...", "weight": 0.7}}
  ],
  "summary": "文档核心摘要（2-3句）"
}}

实体类型可以是：person, organization, market, city, brand, product, channel, platform, policy, risk, event, indicator, concept
关系类型可以是：affects, owns, regulates, competes, cooperates, causes, follows, influences, expands_to, targets, requires, monitors
"""


class GraphBuilder:
    def __init__(self, llm_client: AsyncOpenAI):
        self.llm = llm_client
        self.graph = nx.DiGraph()
        self.entities: list[dict] = []
        self.summary: str = ""

    # ── Build ────────────────────────────────────────────────────────────────

    async def build(self, text: str, prediction_goal: str) -> dict:
        """Extract entities, build graph, return structured data."""
        truncated = text[:8000]  # stay within context
        prompt = _ENTITY_PROMPT.format(text=truncated, goal=prediction_goal)

        try:
            raw = await self._llm_json(prompt)
            data = self._parse_json(raw)
        except Exception as e:
            print(f"[Graph] LLM extraction failed, using rule-based fallback: {e}")
            data = self._fallback_data(truncated, prediction_goal, str(e))

        self.entities = data.get("entities", [])
        self.summary = data.get("summary", "")
        relationships = data.get("relationships", [])

        # Build NetworkX graph
        self.graph.clear()
        for e in self.entities:
            self.graph.add_node(
                e["id"],
                name=e["name"],
                type=e.get("type", "concept"),
                description=e.get("description", ""),
                importance=e.get("importance", 0.5),
            )
        for r in relationships:
            if r["source"] in self.graph and r["target"] in self.graph:
                self.graph.add_edge(
                    r["source"],
                    r["target"],
                    type=r.get("type", "relates"),
                    description=r.get("description", ""),
                    weight=r.get("weight", 0.5),
                )

        print(f"[Graph] Built: {len(self.entities)} entities, {self.graph.number_of_edges()} edges")
        return {
            "entities": self.entities,
            "relationships": relationships,
            "summary": self.summary,
            "stats": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
            },
        }

    # ── Context retrieval ────────────────────────────────────────────────────

    def get_context_for_agent(self, agent_role: str, top_k: int = 5) -> str:
        """Return relevant graph context for a given agent role."""
        if not self.entities:
            return ""

        # Sort by importance, pick top_k
        sorted_ents = sorted(self.entities, key=lambda x: x.get("importance", 0), reverse=True)
        top = sorted_ents[:top_k]

        lines = [f"【知识图谱摘要】{self.summary}", ""]
        for e in top:
            lines.append(f"- {e['name']}（{e['type']}）: {e['description']}")

        return "\n".join(lines)

    def get_graph_data(self) -> dict:
        """Serialise graph for frontend visualisation."""
        nodes = []
        for nid, attrs in self.graph.nodes(data=True):
            nodes.append({"id": nid, **attrs})
        edges = []
        for u, v, attrs in self.graph.edges(data=True):
            edges.append({"source": u, "target": v, **attrs})
        return {"nodes": nodes, "edges": edges}

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _llm_json(self, prompt: str) -> str:
        resp = await self.llm.chat.completions.create(
            model=settings.llm_model_name,
            max_tokens=settings.max_tokens,
            messages=[
                {"role": "system", "content": "你是知识图谱专家，只返回合法 JSON，不含 markdown 代码块。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content or "{}"

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON object
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return {"entities": [], "relationships": [], "summary": "解析失败"}

    @staticmethod
    def _fallback_data(text: str, goal: str, error: str = "") -> dict:
        """Build a small usable graph when the LLM endpoint is temporarily unavailable."""
        keyword_groups = [
            ("market", [
                "东南亚", "新加坡", "马来西亚", "泰国", "越南", "菲律宾", "柬埔寨",
                "日韩", "日本", "韩国", "北美", "美国", "加拿大", "中东", "迪拜",
                "多哈", "澳大利亚", "香港", "中国",
            ]),
            ("brand", [
                "周大福", "Cartier", "Tiffany", "Bvlgari", "Van Cleef", "周生生",
                "六福", "谢瑞麟", "Hearts On Fire", "MONOLOGUE", "SOINLOVE",
                "D-ONE", "T MARK", "传承",
            ]),
            ("product", [
                "黄金", "古法黄金", "钻石", "婚嫁", "珠宝", "首饰", "K金", "IP",
                "联名", "轻奢", "高端钻石",
            ]),
            ("channel", [
                "Shopee", "Lazada", "Amazon", "Rakuten", "Qoo10", "TikTok",
                "Instagram", "YouTube", "Facebook", "小红书", "机场", "购物中心",
                "电商", "直播", "免税", "门店",
            ]),
            ("risk", [
                "金价", "汇率", "通胀", "消费者信心", "关税", "合规", "AML", "KYC",
                "数据隐私", "广告法", "ESG", "供应链", "物流", "监管", "舆情",
            ]),
            ("indicator", ["利率", "客流", "销售", "毛利", "库存", "价格", "旅游"]),
        ]

        haystack = f"{goal}\n{text}".lower()
        entities: list[dict[str, Any]] = []
        seen: set[str] = set()

        for entity_type, keywords in keyword_groups:
            for keyword in keywords:
                if keyword.lower() in haystack and keyword not in seen:
                    seen.add(keyword)
                    entities.append({
                        "id": f"e{len(entities) + 1}",
                        "name": keyword,
                        "type": entity_type,
                        "description": f"从上传材料或 WorldMonitor 信号中识别出的{entity_type}实体：{keyword}",
                        "importance": 0.85 if keyword in {"周大福", "黄金", "金价", "东南亚", "中东"} else 0.65,
                    })

        if not entities:
            entities = [
                {
                    "id": "e1",
                    "name": "周大福海外市场",
                    "type": "concept",
                    "description": "本次战略情报会商的核心业务对象",
                    "importance": 0.9,
                },
                {
                    "id": "e2",
                    "name": "公开市场信号",
                    "type": "event",
                    "description": "来自上传材料或 WorldMonitor 的外部信息",
                    "importance": 0.7,
                },
            ]

        relationships = []
        ctf_id = next((e["id"] for e in entities if e["name"] == "周大福"), entities[0]["id"])
        for entity in entities:
            if entity["id"] == ctf_id:
                continue
            relation_type = "monitors"
            if entity["type"] == "brand":
                relation_type = "competes"
            elif entity["type"] in {"risk", "indicator"}:
                relation_type = "affects"
            elif entity["type"] in {"market", "channel"}:
                relation_type = "targets"
            relationships.append({
                "source": ctf_id,
                "target": entity["id"],
                "type": relation_type,
                "description": f"{entity['name']}需要纳入周大福海外市场战略雷达监控",
                "weight": entity.get("importance", 0.6),
            })

        summary = (
            "已使用本地规则从输入材料中提取市场、品牌、产品、渠道和风险信号，"
            "可继续生成企业专家 Agent 与战略简报。"
        )
        if error:
            summary += f" 真实 LLM 图谱抽取暂不可用：{error}"

        return {"entities": entities, "relationships": relationships, "summary": summary}
