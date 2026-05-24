"""
每日简报任务 — 数据抓取 → 筛选 → 分析 → 生成简报 → 推送
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from models.database import SessionLocal
from models.user import UserConfig
from models.briefing import DailyBriefing, BriefingEvent
from models.alert import AlertRule, AlertLog
from sources.base import IntelEvent
from sources.world_monitor import WorldMonitorSource
from sources.competitor import CompetitorSource
from sources.social_media import SocialMediaSource
from sources.product_trend import ProductTrendSource
from sources.legal_compliance import LegalComplianceSource
from filter.relevance_engine import RelevanceEngine, FilterConfig
from push.email import EmailPushService
from push.feishu import FeishuPushService
from push.wecom import WecomPushService
from push.dingtalk import DingtalkPushService
from config import settings
from intelligence.crew_factory import generate_mock_briefing
from intelligence.llm_client import LLMClient, LLMGenerationError


class DailyBriefingJob:
    """
    每日战略简报任务执行器。
    单例模式，被 APScheduler 每日调用。
    """

    _SOURCES = [
        WorldMonitorSource(),
        CompetitorSource(),
        SocialMediaSource(),
        ProductTrendSource(),
        LegalComplianceSource(),
    ]

    _PUSH_SERVICES = {
        "email": EmailPushService(),
        "feishu": FeishuPushService(),
        "wecom": WecomPushService(),
        "dingtalk": DingtalkPushService(),
    }

    def __init__(self):
        self.filter_engine = RelevanceEngine(FilterConfig(min_relevance=0.5, max_events=25))

    def run(self):
        """
        APScheduler 同步入口。
        由于数据源和推送都是 async，需创建事件循环运行。
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(self._execute())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._execute())

    async def _execute(self):
        """任务主流程。"""
        db = SessionLocal()
        try:
            # 1. 读取用户配置（MVP: 单用户 id=1）
            user = db.query(UserConfig).first()
            if not user:
                print("[DailyBriefing] No user config found, skipping")
                return

            if not user.push_enabled:
                print("[DailyBriefing] Push disabled, skipping")
                return

            user_dict = user.to_dict()
            today = datetime.now().strftime("%Y-%m-%d")
            briefing_id = f"{today.replace('-', '')}-{user.id}"

            # 检查今日是否已生成
            existing = db.query(DailyBriefing).filter_by(briefing_id=briefing_id).first()
            if existing and existing.status == "completed":
                print(f"[DailyBriefing] Briefing {briefing_id} already generated")
                return

            # 2. 创建或更新简报记录
            briefing = db.query(DailyBriefing).filter_by(briefing_id=briefing_id).first()
            if not briefing:
                briefing = DailyBriefing(
                    briefing_id=briefing_id,
                    date=today,
                    status="generating",
                    title=f"每日战略简报 — {today}",
                )
                db.add(briefing)
            else:
                briefing.status = "generating"
                briefing.title = f"每日战略简报 — {today}"
                # 清除旧事件
                db.query(BriefingEvent).filter_by(briefing_id=briefing.id).delete()
            db.commit()
            db.refresh(briefing)

            # 3. 数据采集（并行）
            print(f"[DailyBriefing] Collecting data for user={user.id}...")
            all_events: List[IntelEvent] = []
            for source in self._SOURCES:
                if not source.is_available():
                    continue
                try:
                    events = await source.collect(user_dict, limit=8)
                    all_events.extend(events)
                    print(f"[DailyBriefing]   {source.name}: {len(events)} events")
                except Exception as e:
                    print(f"[DailyBriefing]   {source.name} failed: {e}")

            # 4. 筛选
            filtered = self.filter_engine.filter(all_events, user_dict)
            print(f"[DailyBriefing] Filtered: {len(filtered)}/{len(all_events)} events")

            # 5. 保存事件到数据库
            for ev in filtered:
                be = BriefingEvent(
                    briefing_id=briefing.id,
                    title=ev.title,
                    source=ev.source,
                    category=ev.category,
                    summary=ev.summary,
                    timestamp=ev.timestamp,
                    relevance=ev.relevance,
                    url=ev.url,
                    sources_reference=ev.sources_reference,
                    raw_data={
                        "tags": ev.tags,
                        "sentiment": ev.sentiment,
                        "impact_level": ev.impact_level,
                        "geography": ev.geography,
                    },
                )
                db.add(be)

            # 6. 收集信息源参考
            sources_ref = self._build_sources_reference()

            # 7. 生成简报内容（LLM 或 Mock 降级）
            agent_analyses = self._build_agent_analyses(filtered)

            if settings.is_mock:
                print("[DailyBriefing] Running in MOCK mode")
                content = generate_mock_briefing(
                    topic=f"{user.industry or '综合'}行业每日战略简报",
                    events=[{"title": e.title, "source": e.source, "summary": e.summary, "url": e.url} for e in filtered],
                    agents=agent_analyses,
                    sources_reference=sources_ref,
                )
            else:
                print(f"[DailyBriefing] Running in LLM mode (model={settings.llm_model_name})")
                try:
                    llm = LLMClient()
                    content = await llm.generate_briefing(
                        events=filtered,
                        user_config=user_dict,
                        sources_reference=sources_ref,
                    )
                    print("[DailyBriefing] LLM briefing generated successfully")
                except LLMGenerationError as e:
                    print(f"[DailyBriefing] LLM generation failed, fallback to mock: {e}")
                    content = generate_mock_briefing(
                        topic=f"{user.industry or '综合'}行业每日战略简报",
                        events=[{"title": e.title, "source": e.source, "summary": e.summary, "url": e.url} for e in filtered],
                        agents=agent_analyses,
                        sources_reference=sources_ref,
                    )
                except Exception as e:
                    print(f"[DailyBriefing] Unexpected LLM error, fallback to mock: {e}")
                    content = generate_mock_briefing(
                        topic=f"{user.industry or '综合'}行业每日战略简报",
                        events=[{"title": e.title, "source": e.source, "summary": e.summary, "url": e.url} for e in filtered],
                        agents=agent_analyses,
                        sources_reference=sources_ref,
                    )

            briefing.full_content = content
            # 更健壮的摘要提取：优先从 ## 核心摘要 截取，否则取前 200 字
            if "## 核心摘要" in content:
                try:
                    summary_part = content.split("## 核心摘要", 1)[1]
                    # 找到下一个 ## 标题
                    next_heading_idx = summary_part.find("\n## ")
                    if next_heading_idx > 0:
                        briefing.summary = summary_part[:next_heading_idx].strip().lstrip("\n#:*- ")
                    else:
                        briefing.summary = summary_part.strip().lstrip("\n#:*- ")[:300]
                except Exception:
                    briefing.summary = content[:200]
            else:
                briefing.summary = content[:200]

            briefing.events_count = len(filtered)
            briefing.sources_count = len(set(e.source for e in filtered))
            briefing.agents_count = len(agent_analyses)
            briefing.status = "completed"

            db.commit()
            db.refresh(briefing)
            print(f"[DailyBriefing] Briefing {briefing_id} generated")

            # 7. 检查并触发实时预警
            await self._check_alerts(filtered, briefing.id, db)

            # 8. 推送简报
            await self._push(briefing, user_dict, db)

        except Exception as e:
            print(f"[DailyBriefing] Error: {str(e)}")
            if 'briefing' in locals() and briefing:
                briefing.status = "failed"
                db.commit()
        finally:
            db.close()

    async def _push(self, briefing: DailyBriefing, user_dict: Dict[str, Any], db):
        """向配置的渠道推送简报。"""
        channels = user_dict.get("push_channels", [])
        if not channels:
            print("[DailyBriefing] No push channels configured")
            return

        push_status = {}
        for ch in channels:
            service = self._PUSH_SERVICES.get(ch)
            if not service:
                push_status[ch] = "skipped"
                continue

            result = await service.send(
                title=briefing.title,
                content=briefing.full_content,
                config=user_dict,
            )
            push_status[ch] = "sent" if result.success else "failed"
            print(f"[DailyBriefing] Push {ch}: {result.message}")

        briefing.push_status = push_status
        briefing.pushed_at = datetime.now()
        db.commit()

    @staticmethod
    def _build_agent_analyses(events: List[IntelEvent]) -> List[Dict[str, str]]:
        """根据事件类别构建 Agent 分析摘要。"""
        analyses = []
        category_names = {
            "geopolitics": "地缘政治观察员",
            "market": "市场分析师",
            "policy": "政策研究员",
            "competitor": "竞品情报员",
            "social": "舆情监测员",
            "product": "产品趋势分析师",
            "legal": "合规顾问",
            "tech": "技术观察员",
            "energy": "能源分析师",
        }

        by_cat: Dict[str, List[IntelEvent]] = {}
        for ev in events:
            by_cat.setdefault(ev.category, []).append(ev)

        for cat, cat_events in by_cat.items():
            if not cat_events:
                continue
            top = max(cat_events, key=lambda e: e.relevance)
            analyses.append({
                "name": category_names.get(cat, "情报分析师"),
                "role": f"{cat} 维度分析",
                "insight": f"监测到 {len(cat_events)} 条相关情报，最高相关性事件：「{top.title}」。{top.summary[:80]}...",
            })

        return analyses

    # ── Alert Engine ──

    async def _check_alerts(self, events: List[IntelEvent], briefing_id: int, db):
        """检查事件是否触发预警规则，如触发则创建告警日志并即时推送。"""
        rule = db.query(AlertRule).first()
        if not rule or not rule.enabled:
            return

        # 24h 内已告警的事件去重（按标题+来源）
        cutoff = datetime.now() - __import__('datetime').timedelta(hours=24)
        recent_alerts = db.query(AlertLog).filter(AlertLog.triggered_at >= cutoff).all()
        alerted_keys = {(a.event_title, a.event_source) for a in recent_alerts}

        rule_dict = rule.to_dict()
        keywords = [k.strip().lower() for k in (rule_dict.get("keywords") or []) if k.strip()]
        categories = rule_dict.get("categories") or []
        channels = rule_dict.get("channels") or []
        min_rel = rule_dict.get("min_relevance", 0.85)

        for ev in events:
            # 类别过滤
            if categories and ev.category not in categories:
                continue

            # 去重检查
            if (ev.title, ev.source) in alerted_keys:
                continue

            # 匹配判断
            matched_reason = None
            if ev.relevance >= min_rel:
                matched_reason = "relevance"
            elif keywords:
                text = f"{ev.title} {ev.summary}".lower()
                if any(kw in text for kw in keywords):
                    matched_reason = "keyword"

            if not matched_reason:
                continue

            # 创建 AlertLog
            log = AlertLog(
                rule_id=rule.id,
                event_title=ev.title,
                event_source=ev.source,
                event_category=ev.category,
                event_relevance=ev.relevance,
                event_url=ev.url,
                matched_reason=matched_reason,
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            # 即时推送
            if channels:
                await self._push_alert(log, ev, channels, db)
            else:
                print(f"[Alert] No channels configured for alert #{log.id}")

            alerted_keys.add((ev.title, ev.source))
            print(f"[Alert] Triggered ({matched_reason}): {ev.title[:50]}...")

    async def _push_alert(self, log: AlertLog, event: IntelEvent, channels: List[str], db):
        """推送单条事件告警。"""
        from models.user import UserConfig

        user = db.query(UserConfig).first()
        if not user:
            return
        user_dict = user.to_dict()

        # 构建简短告警内容
        reason_text = ""
        if log.matched_reason == "relevance":
            reason_text = f"相关度 {(event.relevance * 100):.0f}% ≥ 阈值"
        else:
            reason_text = "命中监控关键词"

        content = (
            f"🚨 情报预警\n\n"
            f"标题: {event.title}\n"
            f"来源: {event.source}\n"
            f"类别: {event.category}\n"
            f"触发原因: {reason_text}\n\n"
            f"摘要: {event.summary[:200]}...\n\n"
        )
        if event.url:
            content += f"链接: {event.url}\n"

        push_status = {}
        for ch in channels:
            service = self._PUSH_SERVICES.get(ch)
            if not service:
                push_status[ch] = "skipped"
                continue
            try:
                result = await service.send(
                    title="🚨 情报预警 — " + event.title[:40],
                    content=content,
                    config=user_dict,
                )
                push_status[ch] = "sent" if result.success else "failed"
                print(f"[Alert] Push {ch}: {result.message}")
            except Exception as e:
                push_status[ch] = "failed"
                print(f"[Alert] Push {ch} error: {e}")

        log.push_status = push_status
        log.pushed_at = datetime.now()
        db.commit()

    @staticmethod
    def _build_sources_reference() -> List[Dict[str, Any]]:
        """收集所有数据源的推荐信息源列表。"""
        all_sources = []
        for source in DailyBriefingJob._SOURCES:
            ref = source.get_sources_reference()
            if ref:
                all_sources.append({
                    "category": source.categories[0] if source.categories else source.name,
                    "source_name": source.name,
                    "references": ref,
                })
        return all_sources
