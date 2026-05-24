import type { Brief, EventCard, Simulation } from "../types";

type Props = {
  brief: Brief | null;
  overview: string;
  selectedEvent: EventCard | null;
  simulation: Simulation | null;
  answer: string;
  onAsk: (question: string) => Promise<void>;
  onSimulate: () => Promise<void>;
};

const DEMO_QUESTIONS = [
  "今日五大重点市场里，哪起竞品调价促销事件风险等级最高，判定依据是什么",
  "面对此次竞品促销攻势，不同应对策略分别会产生哪些利弊影响",
  "综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作",
];

export function ChatPanel({ brief, overview, selectedEvent, simulation, answer, onAsk, onSimulate }: Props) {
  const focusMetrics = [
    { label: "高优事件池", value: brief?.top_events.length ?? 0, tone: "blue" },
    { label: "联动岗位", value: Object.keys(brief?.role_actions ?? {}).length, tone: "teal" },
    { label: "策略建议", value: simulation?.options.length ?? 3, tone: "gold" },
  ];

  return (
    <section className="analysis-board panel">
      <div className="panel-top">
        <div>
          <p className="section-kicker">AI Strategy Copilot</p>
          <h2>智能分析师</h2>
          <p className="panel-description">{overview || "等待简报同步完成后开始分析。"}</p>
        </div>
        <button className="primary-button" onClick={() => void onSimulate()}>
          开始模拟
        </button>
      </div>

      <div className="focus-grid">
        <article className="focus-card focus-card-main">
          <div className="focus-card-head">
            <span className="section-kicker">Active Signal</span>
            <span className="market-badge">{selectedEvent?.market ?? "GLOBAL"}</span>
          </div>
          <h3>{selectedEvent?.title ?? "正在等待高优事件"}</h3>
          <p>{selectedEvent?.summary_zh ?? "左侧选择事件后，这里会展示当前聚焦情报、市场摘要与模拟入口。"}</p>
        </article>

        <article className="focus-card trend-card">
          <div className="trend-header">
            <span className="section-kicker">Decision Pulse</span>
            <strong>{simulation ? "已输出策略建议" : "等待推演结果"}</strong>
          </div>
          <div className="pulse-chart" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="metric-mini-grid">
            {focusMetrics.map((item) => (
              <article key={item.label} className={`metric-mini tone-${item.tone}`}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </article>
            ))}
          </div>
        </article>
      </div>

      <div className="question-panel">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Preset Queries</p>
            <h3>快速发问</h3>
          </div>
        </div>
        <div className="question-list">
          {DEMO_QUESTIONS.map((question) => (
            <button key={question} onClick={() => void onAsk(question)}>
              {question}
            </button>
          ))}
        </div>
      </div>

      <article className="answer-box">
        <div className="answer-head">
          <div>
            <p className="section-kicker">Strategy Output</p>
            <h3>智能研判输出</h3>
          </div>
          <span className={`status-dot ${answer ? "ready" : ""}`}>{answer ? "已生成" : "待生成"}</span>
        </div>
        <p>{answer || "选择一个预设问题，或直接开始模拟，系统会结合今日高优事件输出策略判断。"}</p>
      </article>
    </section>
  );
}
