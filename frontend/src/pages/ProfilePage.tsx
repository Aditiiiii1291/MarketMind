import { useState } from "react";

import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";
import { PlaceholderPanel } from "../components/PlaceholderPanel";
import { useAuth } from "../hooks/useAuth";
import { getApiErrorMessage } from "../services/apiError";

export function ProfilePage() {
  const { refreshCurrentUser, user } = useAuth();
  const [error, setError] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  async function handleRefresh() {
    setError("");
    setIsRefreshing(true);

    try {
      await refreshCurrentUser();
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
    } finally {
      setIsRefreshing(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Current-user details are loaded from the existing /auth/me endpoint."
      />
      <PlaceholderPanel title="Signed-in user">
        <ErrorAlert message={error} />
        <dl className="profile-list">
          <div>
            <dt>Username</dt>
            <dd>{user?.username ?? "Unavailable"}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{user?.email ?? "Unavailable"}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{user?.created_at ?? "Unavailable"}</dd>
          </div>
        </dl>
        <button
          className="button button--ghost profile-refresh"
          disabled={isRefreshing}
          onClick={handleRefresh}
          type="button"
        >
          {isRefreshing ? "Refreshing..." : "Refresh profile"}
        </button>
      </PlaceholderPanel>
    </>
  );
}
