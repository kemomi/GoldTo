from app.models import BriefResponse, ChatResponse, SimulationResponse


def _recommended_label(simulation: SimulationResponse) -> str:
    for option in simulation.options:
        if option.option_id == simulation.recommended_option_id:
            return option.label_zh
    return simulation.recommended_option_id


def answer_demo_question(question: str, brief: BriefResponse, simulation: SimulationResponse | None) -> ChatResponse:
    if "风险等级最高" in question:
        if not brief.top_events:
            return ChatResponse(answer="当前简报暂无高风险事件，请稍后刷新今日简报或改问策略利弊。")

        top = brief.top_events[0]
        return ChatResponse(
            answer=f"今天风险最高的是 {top.title}。原因是它发生在核心商圈、涉及婚嫁黄金主力品类，且价格异动达到 {top.price_change_pct}%。",
            cited_event_ids=[top.event_id],
        )
    if "不同应对策略" in question and simulation is not None:
        options = [option for option in simulation.options if option.option_id != "escalate_attention"]
        if not options:
            options = simulation.options
        answer = "；".join(f"{option.label_zh}：{option.rationale}" for option in options)
        return ChatResponse(answer=answer, cited_event_ids=[simulation.event_id])
    if "最优选择" in question and simulation is not None:
        label = _recommended_label(simulation)
        return ChatResponse(
            answer=f"建议选择{label}。{simulation.recommended_reason} 后续由区域运营巡检商圈、市场策略调整婚嫁黄金内容、合规专员复核促销物料。",
            cited_event_ids=[simulation.event_id],
        )
    return ChatResponse(answer="请围绕今日高风险事件、策略利弊或推荐动作提问。")
