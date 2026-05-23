import type { Simulation } from "../types";

type Props = {
  simulation: Simulation | null;
};

export function SimulationPanel({ simulation }: Props) {
  if (!simulation) return <section className="card">点击“开始模拟”查看三类应对级别方案。</section>;

  return (
    <section className="card">
      <h3>三类可选应对级别方案</h3>
      {simulation.options.map((option) => (
        <article key={option.option_id} className="option-card">
          <h4>{option.label_zh}</h4>
          <p>{option.rationale}</p>
          <ul>
            {option.impacts.map((impact) => (
              <li key={`${option.option_id}-${impact.name}`}>
                {impact.name}：{impact.level}，{impact.rationale}
              </li>
            ))}
          </ul>
        </article>
      ))}
      <h3>优选方案及判定理由</h3>
      <p>{simulation.recommended_reason}</p>
      <h4>后续观测与执行提示</h4>
      <ul>
        {simulation.follow_up.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
