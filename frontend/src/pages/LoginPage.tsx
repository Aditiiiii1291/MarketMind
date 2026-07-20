import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { ErrorAlert } from "../components/ErrorAlert";
import { Loading } from "../components/Loading";
import { useAuth } from "../hooks/useAuth";
import { getApiErrorMessage } from "../services/apiError";

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const [email, setEmail] = useState("");
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

    if (!email.includes("@")) {
      setError("Enter a valid email address.");
      return;
    }
    if (password.trim() === "") {
      setError("Password is required.");
      return;
    }

    setIsSubmitting(true);

    try {
      await login({ username_or_email: email.trim(), password });
      navigate(redirectTo, { replace: true });
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
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
            Email
            <input
              autoComplete="email"
              name="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
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

          <ErrorAlert message={error} />

          <button className="button button--primary" disabled={isSubmitting} type="submit">
            {isSubmitting ? <Loading label="Signing in" /> : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          New to MarketMind? <Link to="/register">Create an account</Link>
        </p>
      </section>
    </main>
  );
}
