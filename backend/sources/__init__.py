"""
GoldTo Intelligence Sources — 多维度数据源适配器
"""
from sources.base import DataSource, IntelEvent
from sources.world_monitor import WorldMonitorSource
from sources.competitor import CompetitorSource
from sources.social_media import SocialMediaSource
from sources.product_trend import ProductTrendSource
from sources.legal_compliance import LegalComplianceSource

__all__ = [
    "DataSource", "IntelEvent",
    "WorldMonitorSource", "CompetitorSource", "SocialMediaSource",
    "ProductTrendSource", "LegalComplianceSource",
]
