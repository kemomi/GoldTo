type Props = {
  overview: string;
  answer: string;
  onAsk: (question: string) => Promise<void>;
  onSimulate: () => Promise<void>;
};

const DEMO_QUESTIONS = [
  "今日五大重点市场里，哪起竞品调价促销事件风险等级最高，判定依据是什么",
  "面对此次竞品促销攻势，不同应对策略分别会产生哪些利弊影响",
  "综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作",
];

export function ChatPanel({ overview, answer, onAsk, onSimulate }: Props) {
  return (
    <section>
      <h2>智能分析师</h2>
      <p>{overview}</p>
      <div className="question-list">
        {DEMO_QUESTIONS.map((question) => (
          <button key={question} onClick={() => void onAsk(question)}>
            {question}
          </button>
        ))}
      </div>
      <button onClick={() => void onSimulate()}>开始模拟</button>
      <article className="answer-box">{answer || "选择一个问题或直接开始模拟。"}</article>
    </section>
  );
}
