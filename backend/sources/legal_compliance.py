"""
法律合规数据源 — 监管政策、法律法规变动、行业标准更新
当前为 Mock 模式，后续可接入国家法律法规数据库 RSS
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sources.base import DataSource, IntelEvent
from config import settings


class LegalComplianceSource(DataSource):
    """
    法律与合规监测数据源（Mock）。
    根据用户配置的 industry 生成 Mock 法规变动数据。
    后续可接入：
      - 国家法律法规数据库 RSS
      - 监管公告推送
      - 行业协会发布平台
    """
    name = "legal_compliance"
    categories = ["legal", "policy"]
    recommended_sources = [
        {"name": "国家法律法规数据库", "url": "https://flk.npc.gov.cn", "desc": "中国法律法规权威查询"},
        {"name": "国家市场监督管理总局", "url": "https://www.samr.gov.cn", "desc": "市场监管政策与公告"},
        {"name": "工信部", "url": "https://www.miit.gov.cn", "desc": "信息产业与通信行业政策"},
        {"name": "欧盟委员会", "url": "https://ec.europa.eu", "desc": "欧盟法规与合规要求"},
    ]

    _TEMPLATES = [
        {"title_tpl": "{regulator} 发布 {industry} 行业新规", "summary_tpl": "新规要求 {industry} 企业在 {deadline} 前完成 {requirement}，违规最高罚款 {fine}。", "impact": "high"},
        {"title_tpl": "{industry} 数据安全实施细则征求意见", "summary_tpl": "意见稿对 {scope} 作出详细规定，企业合规成本预计增加 {percent}，征求意见截止 {deadline}。", "impact": "medium"},
        {"title_tpl": "{industry} 反垄断调查进展", "summary_tpl": "{regulator} 对 {company} 涉嫌滥用市场支配地位展开调查，涉及 {area} 业务，或影响行业格局。", "impact": "high"},
        {"title_tpl": "{industry} 出口管制清单更新", "summary_tpl": "新增 {count} 项 {item} 出口限制，相关供应链企业需在 {deadline} 前调整采购策略。", "impact": "medium"},
        {"title_tpl": "跨境 {industry} 服务税务新规生效", "summary_tpl": "新规对 {scope} 征收 {tax_rate} 增值税，跨境服务商需调整定价和 invoicing 流程。", "impact": "medium"},
    ]

    _REGULATORS = ["国家市场监管总局", "工信部", "网信办", "海关总署", "地方金融监管局", "欧盟委员会"]
    _REQUIREMENTS = ["安全评估备案", "算法透明度披露", "用户数据本地化存储", "内容审核机制升级"]
    _SCOPES = ["数据采集范围", "算法推荐机制", "跨境数据传输", "未成年人保护", "消费者权益"]
    _AREAS = ["平台服务", "数据交易", "云服务", "广告业务"]
    _ITEMS = ["高端芯片", "AI 训练设备", "量子计算组件", "生物技术材料"]
    _COMPANIES = ["某头部平台", "某上市公司", "某跨国集团", "某行业龙头"]

    async def collect(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        industry = config.get("industry", "")
        if not industry:
            return []

        # 法律合规数据源暂不支持真实 API（需要接入国家法规数据库）
        # 当 enable_real_sources 为 True 时，如果有真实数据源则优先使用
        # 目前始终返回 Mock 数据
        return await self._collect_mock(industry, limit)

    async def _collect_mock(self, industry: str, limit: int = 10) -> List[IntelEvent]:
        """Mock 数据生成。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()
        templates = random.sample(self._TEMPLATES, k=min(len(self._TEMPLATES), limit))

        for tpl in templates:
            deadline = (now + timedelta(days=random.randint(30, 180))).strftime("%Y年%m月%d日")
            fine = f"{random.randint(100, 2000)} 万元" if random.random() > 0.5 else f"{random.randint(10, 100)} 万美元"

            title = tpl["title_tpl"].format(
                industry=industry,
                regulator=random.choice(self._REGULATORS),
                company=random.choice(self._COMPANIES),
            )
            summary = tpl["summary_tpl"].format(
                industry=industry,
                regulator=random.choice(self._REGULATORS),
                company=random.choice(self._COMPANIES),
                deadline=deadline,
                requirement=random.choice(self._REQUIREMENTS),
                fine=fine,
                scope=random.choice(self._SCOPES),
                percent=f"{random.randint(5, 30)}%",
                area=random.choice(self._AREAS),
                count=random.randint(1, 10),
                item=random.choice(self._ITEMS),
                tax_rate=f"{random.randint(6, 20)}%",
            )

            _URLS = [
                "https://flk.npc.gov.cn",
                "https://www.samr.gov.cn",
                "https://www.miit.gov.cn",
                "https://ec.europa.eu",
            ]
            events.append(IntelEvent(
                title=title,
                source=random.choice(["国家法律法规数据库", "监管公告", "行业协会", "律师事务所", "合规资讯平台"]),
                category="legal",
                summary=summary,
                timestamp=(now - timedelta(hours=random.randint(1, 48))).isoformat() + "Z",
                relevance=round(random.uniform(0.65, 0.95), 2),
                impact_level=tpl["impact"],
                tags=["legal", industry],
                url=random.choice(_URLS),
                sources_reference=self.recommended_sources,
            ))

        return events
