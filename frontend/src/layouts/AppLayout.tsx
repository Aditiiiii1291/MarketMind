import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

const navigationItems = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Products", path: "/products" },
  { label: "Uploads", path: "/uploads" },
  { label: "Analysis", path: "/analysis" },
  { label: "Profile", path: "/profile" }
];

export function AppLayout() {
  const { logout, user } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="sidebar__brand">
          <span className="sidebar__mark">M</span>
          <div>
            <strong>MarketMind</strong>
            <span>Customer intelligence</span>
          </div>
        </div>
        <nav className="sidebar__nav">
          {navigationItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                isActive ? "sidebar__link sidebar__link--active" : "sidebar__link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="app-shell__main">
        <header className="navbar">
          <div>
            <span className="navbar__label">Production frontend</span>
            <strong>{user?.username ?? "MarketMind user"}</strong>
          </div>
          <button className="button button--ghost" type="button" onClick={logout}>
            Logout
          </button>
        </header>

        <main className="content-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
