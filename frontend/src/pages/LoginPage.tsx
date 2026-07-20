import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { Loading } from "../components/Loading";
import { useAuth } from "../hooks/useAuth";

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState | null;
  const redirectTo = state?.from?.pathname ?? "/dashboard";

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login({ username_or_email: usernameOrEmail, password });
      navigate(redirectTo, { replace: true });
    } catch {
      setError("Unable to sign in with those credentials.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card" aria-labelledby="login-title">
        <div className="login-card__intro">
          <span className="sidebar__mark">M</span>
          <p>MarketMind</p>
          <h1 id="login-title">Sign in</h1>
          <span>Use your existing MarketMind API credentials.</span>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            Username or email
            <input
              autoComplete="username"
              name="username_or_email"
              onChange={(event) => setUsernameOrEmail(event.target.value)}
              required
              type="text"
              value={usernameOrEmail}
            />
          </label>

          <label>
            Password
            <input
              autoComplete="current-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="button button--primary" disabled={isSubmitting} type="submit">
            {isSubmitting ? <Loading label="Signing in" /> : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
