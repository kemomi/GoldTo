import type { Brief } from "../types";

type Props = {
  brief: Brief | null;
  selectedEventId: string;
  onSelectEvent: (eventId: string) => void;
};

export function BriefSidebar({ brief, selectedEventId, onSelectEvent }: Props) {
  return (
    <aside className="sidebar">
      <h1>今日战略简报</h1>
      <p>{brief?.overview ?? "正在加载简报..."}</p>
      <h2>高优竞品异动</h2>
      <ul>
        {brief?.top_events.map((event) => (
          <li key={event.event_id}>
            <button className={selectedEventId === event.event_id ? "selected" : ""} onClick={() => onSelectEvent(event.event_id)}>
              {event.title}
            </button>
          </li>
        ))}
      </ul>
      <h2>合规红线提醒</h2>
      <ul>{brief?.compliance_alerts.map((item) => <li key={item}>{item}</li>)}</ul>
      <h2>市场机会看点</h2>
      <ul>{brief?.opportunities.map((item) => <li key={item}>{item}</li>)}</ul>
    </aside>
  );
}
