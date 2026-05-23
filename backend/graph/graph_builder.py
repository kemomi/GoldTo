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
你是一个专业的知识图谱构建专家。请从以下文本中提取关键实体和关系，用于预测分析。

文本：
{text}

预测目标：{goal}

请提取：
- entities: 关键实体（人物、组织、国家、商品、政策、概念等）
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

实体类型可以是：person, organization, country, commodity, policy, concept, event, indicator
关系类型可以是：affects, owns, regulates, competes, cooperates, causes, follows, influences
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

        raw = await self._llm_json(prompt)
        data = self._parse_json(raw)

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
