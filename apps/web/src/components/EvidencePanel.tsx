import type { EventCard } from "../types";

type Props = {
  event: EventCard | null;
};

export function EvidencePanel({ event }: Props) {
  if (!event) return <section className="card">请选择一个高优事件。</section>;

  return (
    <section className="card">
      <h3>事件核心概况</h3>
      <p>{event.summary_zh}</p>
      <a href={event.source_url} target="_blank" rel="noreferrer">
        查看来源
      </a>
    </section>
  );
}
