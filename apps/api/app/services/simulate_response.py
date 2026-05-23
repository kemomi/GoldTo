from app.models import DimensionImpact, EventRecord, SimulationResponse, StrategyOption


def simulate_response(event: EventRecord) -> SimulationResponse:
    if event.confidence < 0.75:
        return SimulationResponse(
            event_id=event.event_id,
            options=[
                StrategyOption(
                    option_id="escalate_attention",
                    label_zh="升级关注",
                    impacts=[DimensionImpact(name="合规风险", level="high", rationale="证据不足，需人工确认。")],
                    rationale="当前证据不完整，不建议直接执行价格动作。",
                )
            ],
            recommended_option_id="escalate_attention",
            recommended_reason="该事件证据不完整，先人工复核再决定是否跟进。",
            follow_up=["补充官方链接或门店公告截图。"],
        )

    options = [
        StrategyOption(
            option_id="hold",
            label_zh="保持不动",
            impacts=[
                DimensionImpact(name="毛利/价格体系压力", level="low", rationale="不调整价格体系。"),
                DimensionImpact(name="客流分流风险", level="high", rationale="核心商圈婚嫁客流可能短期流失。"),
                DimensionImpact(name="品牌调性受损风险", level="low", rationale="不新增促销信号。"),
                DimensionImpact(name="合规风险", level="low", rationale="不新增执行动作。"),
            ],
            rationale="适合影响范围有限或非核心商圈事件。",
        ),
        StrategyOption(
            option_id="local_follow",
            label_zh="局部跟进",
            impacts=[
                DimensionImpact(name="毛利/价格体系压力", level="medium", rationale="仅在受影响商圈做局部回应。"),
                DimensionImpact(name="客流分流风险", level="medium", rationale="可部分对冲竞品短期吸客。"),
                DimensionImpact(name="品牌调性受损风险", level="low", rationale="不破坏全市场高端定位。"),
                DimensionImpact(name="合规风险", level="low", rationale="动作边界可控。"),
            ],
            rationale="适合核心商圈、婚嫁黄金主力品类的高优异动。",
        ),
        StrategyOption(
            option_id="limited_follow",
            label_zh="限时跟进",
            impacts=[
                DimensionImpact(name="毛利/价格体系压力", level="high", rationale="促销更广，价格体系承压。"),
                DimensionImpact(name="客流分流风险", level="low", rationale="短期截留客流能力更强。"),
                DimensionImpact(name="品牌调性受损风险", level="medium", rationale="频繁促销会稀释高端感。"),
                DimensionImpact(name="合规风险", level="medium", rationale="活动文案和门店物料需同步审查。"),
            ],
            rationale="仅适合竞品动作覆盖范围极大且时点紧迫的事件。",
        ),
    ]

    recommended = "local_follow" if event.is_core_district and (event.price_change_pct or 0) >= 5 else "hold"
    if recommended == "local_follow":
        reason = "竞品在核心婚嫁黄金商圈发起 8% 级别促销，局部跟进能平衡客流防守与价格体系压力。"
    else:
        reason = "当前异动未达到核心商圈高优阈值，保持不动更有利于控制价格体系压力并继续观察客流变化。"

    return SimulationResponse(
        event_id=event.event_id,
        options=options,
        recommended_option_id=recommended,
        recommended_reason=reason,
        follow_up=[
            "区域运营今日核查尖沙咀竞品门店活动落地情况。",
            "市场团队同步更新婚嫁黄金内容口径。",
            "合规专员复核临时促销文案与贵金属标识。",
        ],
    )
