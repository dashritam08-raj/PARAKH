import ThemeSelector from "./ThemeSelector";

import {
  NavLink,
  useNavigate,
} from "react-router-dom";

function Sidebar() {
  const navigate =
    useNavigate();

  // ============================================================
  // NAVIGATION ITEMS
  // ============================================================

  const navItems = [
    {
      path: "/",
      label: "Dashboard",
      icon: (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path d="M3 11.5L12 4l9 7.5" />
          <path d="M5.5 10.5V20h13v-9.5" />
          <path d="M9.5 20v-5h5v5" />
        </svg>
      ),
    },

    {
      path: "/inspection",
      label: "New Inspection",
      icon: (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <rect
            x="5"
            y="3"
            width="14"
            height="18"
            rx="2"
          />
          <path d="M9 3.5h6" />
          <path d="M9 9h6" />
          <path d="M9 13h6" />
          <path d="M9 17h3" />
        </svg>
      ),
    },

    {
      path: "/history",
      label: "Inspection History",
      icon: (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path d="M3.5 12a8.5 8.5 0 1 0 2.5-6" />
          <path d="M3.5 5v5h5" />
          <path d="M12 7v5l3 2" />
        </svg>
      ),
    },
  ];

  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {
    localStorage.removeItem(
      "parakh_authenticated"
    );

    navigate(
      "/login",
      {
        replace: true,
      }
    );
  };

  // ============================================================
  // USER
  // ============================================================

  let user = null;

  try {
    user = JSON.parse(
      localStorage.getItem(
        "parakh_user"
      )
    );
  } catch {
    user = null;
  }

  const userName =
    user?.name ||
    "PARAKH Inspector";

  const userRole =
    user?.role ||
    "Inspection Officer";

  const avatar =
    userName
      .charAt(0)
      .toUpperCase();

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <aside className="sidebar">

      {/* ======================================================
          BRAND
      ======================================================= */}

      <div className="sidebar-brand">

        <div className="brand-mark">
          <img
            src="/parakh-logo.jpeg"
            alt="PARAKH Logo"
          />
        </div>

        <div className="brand-text">
          <h2>
            PARAKH
          </h2>

          <span>
            Legal Metrology
          </span>
        </div>

      </div>

      {/* ======================================================
          NAVIGATION
      ======================================================= */}

      <nav className="sidebar-nav">

        <div className="nav-section-title">
          INSPECT
        </div>

        {navItems.map(
          (item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={
                item.path === "/"
              }
              className={({
                isActive,
              }) =>
                `nav-item ${
                  isActive
                    ? "active"
                    : ""
                }`
              }
            >
              <span className="nav-icon">
                {item.icon}
              </span>

              <span className="nav-label">
                {item.label}
              </span>
            </NavLink>
          )
        )}

      </nav>

      {/* ======================================================
          QUICK INSPECTION
      ======================================================= */}

      <div className="sidebar-cta">

        <div className="cta-icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <path d="M12 5v14" />
            <path d="M5 12h14" />
          </svg>
        </div>

        <div className="cta-content">

          <strong>
            Quick Inspection
          </strong>

          <span>
            Analyze a product
          </span>

        </div>

        <button
          type="button"
          className="cta-button"
          onClick={() =>
            navigate(
              "/inspection"
            )
          }
          aria-label="Start inspection"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M5 12h14" />
            <path d="M13 6l6 6-6 6" />
          </svg>
        </button>

      </div>

      {/* ======================================================
          BOTTOM USER AREA
      ======================================================= */}

      <div className="sidebar-theme">
        <ThemeSelector />
      </div>

      <div className="sidebar-bottom">

        <div className="sidebar-user">

          <div className="user-avatar">
            {avatar}
          </div>

          <div className="user-details">

            <strong>
              {userName}
            </strong>

            <span>
              {userRole}
            </span>

          </div>

          <span
            className="online-dot"
            title="System Online"
          />

        </div>

        {/* ==================================================
            LOGOUT
        =================================================== */}

        <button
          type="button"
          className="logout-button"
          onClick={
            handleLogout
          }
        >

          <span className="logout-icon">

            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >
              <path d="M10 17l5-5-5-5" />
              <path d="M15 12H3" />
              <path d="M21 19V5a2 2 0 0 0-2-2h-5" />
            </svg>

          </span>

          <span>
            Sign out
          </span>

        </button>

      </div>

    </aside>
  );
}

export default Sidebar;