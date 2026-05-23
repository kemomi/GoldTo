import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../App";

const api = {
  getBrief: async () => ({
    overview: "今日五大市场整体竞争烈度偏高。",
    top_events: [
      {
        event_id: "hk-csg-pricecut-20260523",
        title: "周生生尖沙咀婚嫁黄金限时 8% 优惠",
        summary_zh: "周生生在香港尖沙咀核心婚嫁商圈推出 8% 限时优惠。",
        market: "HK",
        source_url: "https://example.com/hk-csg-pricecut",
      },
    ],
    compliance_alerts: ["美国贵金属标识与钻石溯源内容需持续关注。"],
    opportunities: ["新加坡高端婚嫁珠宝内容热度可作为新品观察线索。"],
    role_actions: {
      hq: "总部管理层重点关注香港核心商圈应对级别是否上收决策。",
      ops: "区域运营今日优先巡检尖沙咀商圈并准备局部促销预案。",
      marketing: "市场策略岗同步检查婚嫁黄金内容方向与投放素材。",
    },
    manual_review: [],
  }),
  getThresholds: async () => ({ must_report_price_change_pct: 5, optional_price_change_pct: 2 }),
  updateThresholds: async () => ({ must_report_price_change_pct: 6, optional_price_change_pct: 3 }),
  simulateEvent: async () => ({
    event_id: "hk-csg-pricecut-20260523",
    recommended_option_id: "local_follow",
    recommended_reason: "局部跟进能平衡客流防守与价格体系压力。",
    follow_up: ["区域运营巡检尖沙咀。"],
    options: [],
  }),
  askQuestion: async () => ({ answer: "建议选择局部跟进。", cited_event_ids: ["hk-csg-pricecut-20260523"] }),
};

describe("App", () => {
  it("renders the top event and simulate action", async () => {
    render(<App api={api as never} />);

    expect(await screen.findByText("周生生尖沙咀婚嫁黄金限时 8% 优惠")).toBeTruthy();
    expect(screen.getByRole("button", { name: "开始模拟" })).toBeTruthy();
    expect(screen.getByText("今日五大市场整体竞争烈度偏高。")).toBeTruthy();
  });
});
