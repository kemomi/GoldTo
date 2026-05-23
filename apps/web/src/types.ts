export type Thresholds = {
  must_report_price_change_pct: number;
  optional_price_change_pct: number;
};

export type EventCard = {
  event_id: string;
  title: string;
  summary_zh: string;
  market: string;
  source_url: string;
};

export type Brief = {
  overview: string;
  top_events: EventCard[];
  compliance_alerts: string[];
  opportunities: string[];
  role_actions: Record<string, string>;
  manual_review: EventCard[];
};

export type Simulation = {
  event_id: string;
  recommended_option_id: string;
  recommended_reason: string;
  follow_up: string[];
  options: Array<{
    option_id: string;
    label_zh: string;
    rationale: string;
    impacts: Array<{ name: string; level: string; rationale: string }>;
  }>;
};

export type ChatAnswer = {
  answer: string;
  cited_event_ids: string[];
};
