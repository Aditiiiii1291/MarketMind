import { PageHeader } from "../components/PageHeader";
import { PlaceholderPanel } from "../components/PlaceholderPanel";
import { useAuth } from "../hooks/useAuth";

export function ProfilePage() {
  const { user } = useAuth();

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Current-user details are loaded from the existing /auth/me endpoint."
      />
      <PlaceholderPanel title="Signed-in user">
        <dl className="profile-list">
          <div>
            <dt>Username</dt>
            <dd>{user?.username ?? "Unavailable"}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{user?.email ?? "Unavailable"}</dd>
          </div>
        </dl>
      </PlaceholderPanel>
    </>
  );
}
