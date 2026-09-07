import "./SplashScreen.css";

function SplashScreen() {
  return (
    <div className="parakh-splash">

      <div className="splash-grid" />

      <div className="splash-glow splash-glow-one" />
      <div className="splash-glow splash-glow-two" />


      {/* Rotating inspection rings */}
      <div className="splash-rings">

        <div className="splash-ring ring-one" />
        <div className="splash-ring ring-two" />
        <div className="splash-ring ring-three" />

      </div>


      {/* Logo */}
      <div className="splash-logo-container">

        <div className="splash-scan-line" />

        <img
          src="/parakh-logo.jpeg"
          alt="PARAKH"
          className="splash-logo"
        />

      </div>


      {/* Brand */}
      <div className="splash-brand">

        <h1>PARAKH</h1>

        <p>
          AI-POWERED LEGAL METROLOGY
        </p>

      </div>


      {/* System status */}
      <div className="splash-status">

        <span className="status-pulse" />

        <span>
          INSPECTION ENGINE INITIALIZING
        </span>

      </div>


      {/* Progress */}
      <div className="splash-progress">

        <div className="splash-progress-bar" />

      </div>


      <div className="splash-footer">

        <span>
          SCAN
        </span>

        <span>•</span>

        <span>
          ANALYZE
        </span>

        <span>•</span>

        <span>
          VERIFY
        </span>

        <span>•</span>

        <span>
          REPORT
        </span>

      </div>

    </div>
  );
}

export default SplashScreen;