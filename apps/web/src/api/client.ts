import type { Brief, ChatAnswer, Simulation, Thresholds } from "../types";

const API_BASE = "http://localhost:8000";

export const api = {
  async getBrief(): Promise<Brief> {
    const response = await fetch(`${API_BASE}/api/briefs/today`);
    return response.json();
  },
  async simulateEvent(eventId: string): Promise<Simulation> {
    const response = await fetch(`${API_BASE}/api/events/${eventId}/simulate`, { method: "POST" });
    return response.json();
  },
  async askQuestion(question: string): Promise<ChatAnswer> {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    return response.json();
  },
  async getThresholds(): Promise<Thresholds> {
    const response = await fetch(`${API_BASE}/api/config/thresholds`);
    return response.json();
  },
  async updateThresholds(payload: Thresholds): Promise<Thresholds> {
    const response = await fetch(`${API_BASE}/api/config/thresholds`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.json();
  },
};
