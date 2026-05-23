import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "../App";
import type { Brief } from "../types";

const initialBrief: Brief = {
  overview: "Initial overview",
  top_events: [
    {
      event_id: "event-initial",
      title: "Initial top event",
      summary_zh: "Initial summary",
      market: "US",
      source_url: "https://example.com/initial",
    },
    {
      event_id: "event-secondary",
      title: "Secondary event",
      summary_zh: "Secondary summary",
      market: "US",
      source_url: "https://example.com/secondary",
    },
  ],
  compliance_alerts: ["Initial compliance"],
  opportunities: ["Initial opportunity"],
  role_actions: {
    hq: "HQ action",
    ops: "Ops action",
    marketing: "Marketing action",
  },
  manual_review: [],
};

const refreshedBrief: Brief = {
  overview: "Refreshed overview",
  top_events: [
    {
      event_id: "event-refreshed",
      title: "Refreshed top event",
      summary_zh: "Refreshed summary",
      market: "US",
      source_url: "https://example.com/refreshed",
    },
  ],
  compliance_alerts: ["Refreshed compliance"],
  opportunities: ["Refreshed opportunity"],
  role_actions: {
    hq: "HQ action refreshed",
    ops: "Ops action refreshed",
    marketing: "Marketing action refreshed",
  },
  manual_review: [],
};

describe("App threshold save refresh", () => {
  it("refreshes the brief and resets stale result state after saving thresholds", async () => {
    const getBrief = vi.fn<() => Promise<Brief>>().mockResolvedValueOnce(initialBrief).mockResolvedValueOnce(refreshedBrief);
    const simulateEvent = vi.fn(async (eventId: string) => ({
      event_id: eventId,
      recommended_option_id: "local_follow",
      recommended_reason: `Simulation for ${eventId}`,
      follow_up: [`Follow up for ${eventId}`],
      options: [],
    }));
    const askQuestion = vi.fn(async () => ({
      answer: "Stale answer",
      cited_event_ids: ["event-initial"],
    }));

    const api = {
      getBrief,
      getThresholds: async () => ({ must_report_price_change_pct: 5, optional_price_change_pct: 2 }),
      updateThresholds: async () => ({ must_report_price_change_pct: 6, optional_price_change_pct: 3 }),
      simulateEvent,
      askQuestion,
    };

    const { container } = render(<App api={api as never} />);

    expect(await screen.findByText("Initial top event")).toBeTruthy();

    const firstQuestionButton = container.querySelector(".question-list button");
    const simulateButton = container.querySelector(".center-panel section > button:last-of-type");
    const saveButton = container.querySelector(".right-panel .card button");

    if (!firstQuestionButton || !simulateButton || !saveButton) {
      throw new Error("Expected app controls to be rendered");
    }

    fireEvent.click(firstQuestionButton);
    expect(await screen.findByText("Stale answer")).toBeTruthy();

    fireEvent.click(simulateButton);
    expect(await screen.findByText("Simulation for event-initial")).toBeTruthy();

    const secondaryEventButton = screen.getByRole("button", { name: "Secondary event" });
    fireEvent.click(secondaryEventButton);
    fireEvent.click(saveButton);

    await waitFor(() => expect(getBrief).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Refreshed top event")).toBeTruthy();
    expect(screen.queryByText("Stale answer")).toBeNull();
    expect(screen.queryByText("Simulation for event-initial")).toBeNull();
    expect(screen.getByRole("button", { name: "Refreshed top event" }).className).toContain("selected");

    fireEvent.click(simulateButton);

    await waitFor(() => {
      expect(simulateEvent).toHaveBeenLastCalledWith("event-refreshed");
    });
    expect(await screen.findByText("Simulation for event-refreshed")).toBeTruthy();
  });
});
