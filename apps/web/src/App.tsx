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
  const handleSelectEvent = (eventId: string) => {
    if (eventId === selectedEventId) return;
    setSelectedEventId(eventId);
    setSimulation(null);
    setAnswer("");
  };

  return (
    <div className="layout">
      <BriefSidebar brief={sidebarBrief} selectedEventId={selectedEventId} onSelectEvent={handleSelectEvent} />
      <main className="center-panel">
        <ChatPanel
          overview={brief?.overview ?? ""}
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
  );
}
