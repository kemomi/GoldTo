import { useEffect, useState } from "react";

import type { Brief, Simulation, Thresholds } from "./types";
import { api as defaultApi } from "./api/client";
import { BriefSidebar } from "./components/BriefSidebar";
import { ChatPanel } from "./components/ChatPanel";
import { EvidencePanel } from "./components/EvidencePanel";
import { SimulationPanel } from "./components/SimulationPanel";
import { ThresholdPanel } from "./components/ThresholdPanel";

type AppProps = {
  api?: typeof defaultApi;
};

export function App({ api = defaultApi }: AppProps) {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [answer, setAnswer] = useState<string>("");
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);

  useEffect(() => {
    void api.getBrief().then((result) => {
      setBrief(result);
      setSelectedEventId(result.top_events[0]?.event_id ?? "");
    });
    void api.getThresholds().then(setThresholds);
  }, [api]);

  const selectedEvent = brief?.top_events.find((event) => event.event_id === selectedEventId) ?? null;
  const sidebarBrief = brief ? { ...brief, overview: `${brief.overview}\u2060` } : null;
  const activeMarkets = Array.from(new Set(brief?.top_events.map((event) => event.market) ?? []));
  const metricCards = [
    { label: "高优事件", value: brief?.top_events.length ?? 0, hint: "实时监测" },
    { label: "覆盖市场", value: activeMarkets.length, hint: activeMarkets.join(" / ") || "等待同步" },
    { label: "合规提醒", value: brief?.compliance_alerts.length ?? 0, hint: "需联动复核" },
    { label: "机会线索", value: brief?.opportunities.length ?? 0, hint: "可转策略动作" },
  ];
  const handleSelectEvent = (eventId: string) => {
    if (eventId === selectedEventId) return;
    setSelectedEventId(eventId);
    setSimulation(null);
    setAnswer("");
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-copy">
          <p className="eyebrow">Overseas Jewelry Strategy Simulator</p>
          <h1>海外珠宝竞对策略驾驶舱</h1>
          <p className="header-summary">{brief?.overview ?? "正在同步全球市场战报、竞品价格异动与策略信号..."}</p>
        </div>
        <div className="header-status">
          <div className="status-chip">
            <span className="status-label">监控状态</span>
            <strong>LIVE</strong>
          </div>
          <div className="status-chip">
            <span className="status-label">当前焦点</span>
            <strong>{selectedEvent?.market ?? "GLOBAL"}</strong>
          </div>
          <div className="status-chip">
            <span className="status-label">模拟进度</span>
            <strong>{simulation ? "已生成" : "待推演"}</strong>
          </div>
        </div>
        <div className="metric-strip">
          {metricCards.map((item) => (
            <article key={item.label} className="metric-card">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              <small>{item.hint}</small>
            </article>
          ))}
        </div>
      </header>
      <div className="layout">
        <BriefSidebar brief={sidebarBrief} selectedEventId={selectedEventId} onSelectEvent={handleSelectEvent} />
        <main className="center-panel">
        <ChatPanel
          overview={brief?.overview ?? ""}
          brief={brief}
          selectedEvent={selectedEvent}
          simulation={simulation}
          answer={answer}
          onAsk={async (question) => {
            const result = await api.askQuestion(question);
            setAnswer(result.answer);
          }}
          onSimulate={async () => {
            if (!selectedEventId) return;
            setSimulation(await api.simulateEvent(selectedEventId));
          }}
        />
        </main>
        <aside className="right-panel">
          <ThresholdPanel
            thresholds={thresholds}
            onSave={async (next) => {
              const saved = await api.updateThresholds(next);
              const refreshedBrief = await api.getBrief();
              setThresholds(saved);
              setBrief(refreshedBrief);
              setSelectedEventId(refreshedBrief.top_events[0]?.event_id ?? "");
              setSimulation(null);
              setAnswer("");
            }}
          />
          <EvidencePanel event={selectedEvent} />
          <SimulationPanel simulation={simulation} />
        </aside>
      </div>
    </div>
  );
}
