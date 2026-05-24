import type { Simulation } from "../types";

type Props = {
  simulation: Simulation | null;
};

function levelClass(level: string): string {
  const normalized = level.toLowerCase();
  if (normalized.includes("high") || normalized.includes("高")) return "high";
  if (normalized.includes("medium") || normalized.includes("mid") || normalized.includes("中")) return "medium";
  return "low";
}

export function SimulationPanel({ simulation }: Props) {
  if (!simulation) return <section className="card plan-card empty-card">点击“开始模拟”查看三类应对级别方案。</section>;

  return (
    <section className="card plan-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Scenario Planning</p>
          <h3>三类可选应对级别方案</h3>
        </div>
      </div>
      {simulation.options.map((option) => (
        <article
          key={option.option_id}
          className={`option-card ${simulation.recommended_option_id === option.option_id ? "recommended" : ""}`}
        >
          <div className="option-head">
            <h4>{option.label_zh}</h4>
            {simulation.recommended_option_id === option.option_id ? <span className="recommended-badge">优选</span> : null}
          </div>
          <p>{option.rationale}</p>
          <ul className="impact-list">
            {option.impacts.map((impact) => (
              <li key={`${option.option_id}-${impact.name}`}>
                <span>{impact.name}</span>
                <em className={`impact-pill ${levelClass(impact.level)}`}>{impact.level}</em>
                <p>{impact.rationale}</p>
              </li>
            ))}
          </ul>
        </article>
      ))}

      <article className="recommendation-card">
        <p className="section-kicker">Recommended Strategy</p>
        <h4>优选方案及判定理由</h4>
        <p>{simulation.recommended_reason}</p>
      </article>

      <div className="section-heading compact">
        <div>
          <p className="section-kicker">Follow Up</p>
          <h4>后续观测与执行提示</h4>
        </div>
      </div>
      <ul className="bullet-list follow-list">
        {simulation.follow_up.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
