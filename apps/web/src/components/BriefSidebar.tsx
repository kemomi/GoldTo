import type { Brief } from "../types";

type Props = {
  brief: Brief | null;
  selectedEventId: string;
  onSelectEvent: (eventId: string) => void;
};

const ROLE_LABELS: Record<string, string> = {
  hq: "总部决策",
  ops: "区域运营",
  marketing: "市场策略",
};

export function BriefSidebar({ brief, selectedEventId, onSelectEvent }: Props) {
  const topEvents = brief?.top_events ?? [];
  const roleActions = Object.entries(brief?.role_actions ?? {});

  return (
    <aside className="sidebar panel">
      <section className="hero-card">
        <p className="section-kicker">今日战报摘要</p>
        <h2>全球竞对态势总览</h2>
        <p className="hero-copy">{brief?.overview ?? "正在加载简报..."}</p>
        <div className="signal-grid">
          <article>
            <span>重点信号</span>
            <strong>{topEvents.length}</strong>
          </article>
          <article>
            <span>人工复核</span>
            <strong>{brief?.manual_review.length ?? 0}</strong>
          </article>
        </div>
      </section>

      <section className="sidebar-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Priority Feed</p>
            <h3>高优竞品异动</h3>
          </div>
          <span className="section-count">{topEvents.length.toString().padStart(2, "0")}</span>
        </div>
        <div className="event-stack">
          {topEvents.map((event, index) => (
            <button
              key={event.event_id}
              className={`event-card ${selectedEventId === event.event_id ? "selected" : ""}`}
              onClick={() => onSelectEvent(event.event_id)}
            >
              <div className="event-card-meta">
                <span>0{index + 1}</span>
                <span className="market-badge">{event.market}</span>
              </div>
              <strong>{event.title}</strong>
              <p>{event.summary_zh}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="sidebar-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Guardrails</p>
            <h3>合规与机会雷达</h3>
          </div>
        </div>
        <div className="insight-columns">
          <article className="sub-card">
            <h4>合规红线提醒</h4>
            <ul className="bullet-list">
              {brief?.compliance_alerts.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
          <article className="sub-card">
            <h4>市场机会看点</h4>
            <ul className="bullet-list">
              {brief?.opportunities.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>
        </div>
      </section>

      <section className="sidebar-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Action Matrix</p>
            <h3>岗位联动建议</h3>
          </div>
        </div>
        <div className="role-grid">
          {roleActions.map(([role, action]) => (
            <article key={role} className="role-card">
              <span>{ROLE_LABELS[role] ?? role}</span>
              <p>{action}</p>
            </article>
          ))}
        </div>
      </section>
    </aside>
  );
}
