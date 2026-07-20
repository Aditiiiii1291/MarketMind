import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { ErrorAlert } from "../components/ErrorAlert";
import { Loading } from "../components/Loading";
import { SuccessAlert } from "../components/SuccessAlert";
import { useAuth } from "../hooks/useAuth";
import { getApiErrorMessage } from "../services/apiError";

export function RegisterPage() {
  const { isAuthenticated, register } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  function validateForm(): string {
    if (username.trim() === "") {
      return "Username is required.";
    }
    if (!email.includes("@")) {
      return "Enter a valid email address.";
    }
    if (password.length < 8) {
      return "Password must be at least 8 characters long.";
    }
    if (password !== confirmPassword) {
      return "Passwords do not match.";
    }

    return "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password
      });
      setSuccess("Account created. You can sign in now.");
      setUsername("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-card" aria-labelledby="register-title">
        <div className="login-card__intro">
          <span className="sidebar__mark">M</span>
          <p>MarketMind</p>
          <h1 id="register-title">Create account</h1>
          <span>Register with the existing MarketMind API.</span>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            Username
            <input
              autoComplete="username"
              name="username"
              onChange={(event) => setUsername(event.target.value)}
              required
              type="text"
              value={username}
            />
          </label>

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
              autoComplete="new-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>

          <label>
            Confirm password
            <input
              autoComplete="new-password"
              name="confirm_password"
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
              type="password"
              value={confirmPassword}
            />
          </label>

          <ErrorAlert message={error} />
          <SuccessAlert message={success} />

          <button className="button button--primary" disabled={isSubmitting} type="submit">
            {isSubmitting ? <Loading label="Creating account" /> : "Create account"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
