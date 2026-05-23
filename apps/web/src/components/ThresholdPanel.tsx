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
    <section className="card">
      <h3>价格异动阈值</h3>
      <label>
        必须上报阈值
        <input type="number" value={form.must_report_price_change_pct} onChange={(event) => setForm({ ...form, must_report_price_change_pct: Number(event.target.value) })} />
      </label>
      <label>
        可选上报阈值
        <input type="number" value={form.optional_price_change_pct} onChange={(event) => setForm({ ...form, optional_price_change_pct: Number(event.target.value) })} />
      </label>
      <button onClick={() => void onSave(form)}>保存阈值</button>
    </section>
  );
}
