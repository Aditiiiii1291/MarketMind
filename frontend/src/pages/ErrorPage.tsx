import { Link } from "react-router-dom";

export function ErrorPage() {
  return (
    <main className="error-page">
      <section className="error-page__content">
        <p>404</p>
        <h1>Page not found</h1>
        <span>The requested MarketMind route does not exist.</span>
        <Link className="button button--primary" to="/dashboard">
          Go to dashboard
        </Link>
      </section>
    </main>
  );
}
