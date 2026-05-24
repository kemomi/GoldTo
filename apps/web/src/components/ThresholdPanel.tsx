import { useEffect, useState } from "react";

import type { Thresholds } from "../types";

type Props = {
  thresholds: Thresholds | null;
  onSave: (next: Thresholds) => Promise<void>;
};

export function ThresholdPanel({ thresholds, onSave }: Props) {
  const [form, setForm] = useState<Thresholds>({ must_report_price_change_pct: 5, optional_price_change_pct: 2 });

  useEffect(() => {
    if (thresholds) setForm(thresholds);
  }, [thresholds]);

  return (
    <section className="card control-card">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Control Tower</p>
          <h3>价格异动阈值</h3>
        </div>
      </div>
      <p className="card-description">调整上报阈值后会重新刷新简报，让高优事件池与策略建议同步更新。</p>
      <label className="field">
        <span>必须上报阈值</span>
        <div className="input-shell">
          <input
            type="number"
            value={form.must_report_price_change_pct}
            onChange={(event) => setForm({ ...form, must_report_price_change_pct: Number(event.target.value) })}
          />
          <em>%</em>
        </div>
      </label>
      <label className="field">
        <span>可选上报阈值</span>
        <div className="input-shell">
          <input
            type="number"
            value={form.optional_price_change_pct}
            onChange={(event) => setForm({ ...form, must_report_price_change_pct: form.must_report_price_change_pct, optional_price_change_pct: Number(event.target.value) })}
          />
          <em>%</em>
        </div>
      </label>
      <button className="secondary-button" onClick={() => void onSave(form)}>
        保存阈值
      </button>
    </section>
  );
}
