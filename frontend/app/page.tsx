export default function HomePage() {
  return (
    <section className="stack">
      <header className="section-intro reveal">
        <p className="eyebrow">Overview</p>
        <h1 className="headline">Minimal process intelligence. Maximum privacy discipline.</h1>
        <p className="subtitle">
          OCG combines Slack, Jira, and GitHub metadata into actionable process views while
          keeping fail-closed permissions and k-anonymous analytics as strict defaults.
        </p>
      </header>
      <div className="panel-grid">
        <article className="panel reveal">
          <h2 className="panel-title">Admin</h2>
          <p className="kicker">Control connectors, monitor health, and tune retention safely.</p>
        </article>
        <article className="panel reveal">
          <h2 className="panel-title">Analytics</h2>
          <p className="kicker">Inspect published variants, bottlenecks, and next-step probabilities.</p>
        </article>
        <article className="panel reveal">
          <h2 className="panel-title">Personal</h2>
          <p className="kicker">View your private timeline and tasks with explicit opt-in aggregation.</p>
        </article>
      </div>
    </section>
  );
}
