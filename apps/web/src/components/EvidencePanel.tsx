import type { EventCard } from "../types";

type Props = {
  event: EventCard | null;
};

function getSourceHost(url: string): string {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

const SOURCE_TYPE_LABELS: Record<string, string> = {
  competitor_official: "竞品官方",
  mall_official: "商场官方",
  platform_announcement: "平台公告",
  regulation_update: "合规更新",
  industry_news: "行业新闻",
  seeded_media: "预置媒体",
};

const FETCH_STATUS_LABELS: Record<string, string> = {
  live: "实时抓取",
  fixture_fallback: "降级到本地证据",
};

export function EvidencePanel({ event }: Props) {
  if (!event) return <section className="card info-card empty-card">请选择一个高优事件。</section>;

  return (
    <section className="card info-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Evidence Snapshot</p>
          <h3>事件核心概况</h3>
        </div>
        <span className="market-badge">{event.market}</span>
      </div>
      <h4>{event.title}</h4>
      <p>{event.summary_zh}</p>
      <div className="source-meta">
        <span>来源站点</span>
        <strong>{getSourceHost(event.source_url)}</strong>
      </div>
      <div className="source-meta">
        <span>来源类型</span>
        <strong>{SOURCE_TYPE_LABELS[event.source_type] ?? event.source_type}</strong>
      </div>
      <div className="source-meta">
        <span>抓取状态</span>
        <strong>{FETCH_STATUS_LABELS[event.fetch_status] ?? event.fetch_status}</strong>
      </div>
      {event.fallback_reason ? (
        <div className="source-meta">
          <span>降级原因</span>
          <strong>{event.fallback_reason}</strong>
        </div>
      ) : null}
      <a href={event.source_url} target="_blank" rel="noreferrer">
        查看来源
      </a>
    </section>
  );
}
