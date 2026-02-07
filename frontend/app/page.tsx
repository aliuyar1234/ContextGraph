export default function HomePage() {
  return (
    <section>
      <h1 className="headline">Open Context Graph</h1>
      <p>
        Privacy-aware process intelligence built from Slack, Jira, and GitHub metadata with
        fail-closed permissions and k-anonymous analytics.
      </p>
      <div className="grid">
        <article className="card">
          <h3>Admin</h3>
          <p>Enable connectors, view health, and tune retention safely.</p>
        </article>
        <article className="card">
          <h3>Analytics</h3>
          <p>Explore published process variants, bottlenecks, and next-step probabilities.</p>
        </article>
        <article className="card">
          <h3>Personal</h3>
          <p>View your private timeline and tasks, with explicit opt-in for aggregation.</p>
        </article>
      </div>
    </section>
  );
}

