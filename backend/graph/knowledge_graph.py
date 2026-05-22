"""GraphRAG-style knowledge graph built from seed material."""
import re, json, hashlib, networkx as nx
from dataclasses import dataclass, field
from typing import Optional
from utils.llm_client import llm

@dataclass
class Entity:
    id: str
    label: str
    type: str          # person | org | concept | event | price
    description: str = ""
    properties: dict  = field(default_factory=dict)

@dataclass
class Relation:
    source: str
    target: str
    label: str
    weight: float = 1.0


class KnowledgeGraph:
    def __init__(self):
        self.G = nx.DiGraph()
        self.entities: dict[str, Entity] = {}
        self.relations: list[Relation] = []

    # ─── build ─────────────────────────────────────────────────────────────
    def build_from_text(self, text: str) -> dict:
        """Extract entities & relations via LLM, build graph."""
        prompt = f"""从以下文本中提取实体和关系，返回JSON（只返回JSON，不要其他内容）：
{{
  "entities": [
    {{"id":"e1","label":"名称","type":"person|org|concept|event|price","description":"简短描述"}}
  ],
  "relations": [
    {{"source":"e1","target":"e2","label":"关系描述","weight":0.8}}
  ]
}}

文本：
{text[:3000]}"""
        result = llm.json_chat([{"role": "user", "content": prompt}],
                               system="你是知识图谱构建专家。只输出JSON。")
        if "entities" not in result:
            result = self._fallback_extract(text)

        for e in result.get("entities", []):
            eid = e.get("id") or hashlib.md5(e["label"].encode()).hexdigest()[:8]
            entity = Entity(id=eid, label=e["label"], type=e.get("type","concept"),
                            description=e.get("description",""))
            self.entities[eid] = entity
            self.G.add_node(eid, **{"label": entity.label, "type": entity.type,
                                    "description": entity.description})

        for r in result.get("relations", []):
            if r["source"] in self.G and r["target"] in self.G:
                rel = Relation(r["source"], r["target"], r["label"],
                               float(r.get("weight", 1.0)))
                self.relations.append(rel)
                self.G.add_edge(r["source"], r["target"],
                                label=r["label"], weight=rel.weight)

        return self.to_dict()

    # ─── query ─────────────────────────────────────────────────────────────
    def get_neighbors(self, entity_id: str, depth: int = 2) -> list[str]:
        try:
            nodes = nx.single_source_shortest_path_length(self.G, entity_id, cutoff=depth)
            return list(nodes.keys())
        except Exception:
            return []

    def get_context_for_agent(self, agent_type: str) -> str:
        """Return relevant graph context for a given agent type."""
        relevant = [e for e in self.entities.values()
                    if agent_type.lower() in e.description.lower()
                    or agent_type.lower() in e.type.lower()]
        if not relevant:
            relevant = list(self.entities.values())[:5]
        lines = [f"- {e.label} ({e.type}): {e.description}" for e in relevant[:8]]
        return "\n".join(lines)

    # ─── serialization ─────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        nodes = [{"id": n, "label": d.get("label",""), "type": d.get("type","concept"),
                  "description": d.get("description","")}
                 for n, d in self.G.nodes(data=True)]
        edges = [{"source": u, "target": v, "label": d.get("label",""),
                  "weight": d.get("weight", 1.0)}
                 for u, v, d in self.G.edges(data=True)]
        return {"nodes": nodes, "edges": edges}

    # ─── fallback ──────────────────────────────────────────────────────────
    def _fallback_extract(self, text: str) -> dict:
        """Simple regex-based extraction when LLM unavailable."""
        # Detect price patterns
        prices = re.findall(r'\$[\d,]+(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:美元|元|USD)', text)
        entities, relations = [], []
        seen = set()
        for i, p in enumerate(prices[:5]):
            eid = f"price_{i}"
            if p not in seen:
                entities.append({"id": eid, "label": p, "type": "price",
                                  "description": f"价格信号: {p}"})
                seen.add(p)
        # Detect org/name patterns (Chinese)
        orgs = re.findall(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)*|[\u4e00-\u9fa5]{2,4}(?:公司|银行|基金|储备)', text)
        for i, o in enumerate(orgs[:8]):
            eid = f"org_{i}"
            if o not in seen:
                entities.append({"id": eid, "label": o, "type": "org",
                                  "description": f"机构: {o}"})
                seen.add(o)
        # Basic relations
        if len(entities) >= 2:
            relations = [{"source": entities[0]["id"], "target": entities[1]["id"],
                          "label": "影响", "weight": 0.7}]
        return {"entities": entities or [{"id":"e0","label":"市场","type":"concept","description":"整体市场"}],
                "relations": relations}
