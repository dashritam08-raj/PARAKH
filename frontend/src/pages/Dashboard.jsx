import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import "./Dashboard.css";


import { API_BASE_URL } from "../config/api";


function Dashboard() {

  const navigate =
    useNavigate();


  // ============================================================
  // USER + LIVE CLOCK
  // ============================================================

  const [currentTime, setCurrentTime] =
    useState(new Date());

  const [userName, setUserName] =
    useState("Inspector");


  useEffect(() => {

    // Get logged-in user
    try {

      const savedUser =
        localStorage.getItem(
          "parakh_user"
        );


      if (savedUser) {

        const user =
          JSON.parse(savedUser);


        setUserName(
          user?.name ||
          "Inspector"
        );

      }

    } catch (error) {

      console.error(
        "Unable to read logged-in user:",
        error
      );

    }


    // Live clock
    const timer =
      setInterval(() => {

        setCurrentTime(
          new Date()
        );

      }, 1000);


    return () => {

      clearInterval(timer);

    };

  }, []);


  // ============================================================
  // HISTORY STATE
  // ============================================================

  const [
    inspections,
    setInspections,
  ] = useState([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  // ============================================================
  // LOAD HISTORY
  // ============================================================

  useEffect(() => {

    loadHistory();

  }, []);


  const loadHistory =
    async () => {

      setLoading(true);
      setError("");


      try {

        const response =
          await fetch(
            `${API_BASE_URL}/history`,
            {
              credentials: "include",
            }
          );


        if (!response.ok) {

          throw new Error(
            "Unable to load inspection history."
          );

        }


        const data =
          await response.json();


        /*
          Backend may return:

          [
            {...},
            {...}
          ]

          OR

          {
            inspections: [...]
          }

          OR

          {
            history: [...]
          }
        */

        const records =
          Array.isArray(data)
            ? data
            : Array.isArray(
                data?.inspections
              )
              ? data.inspections
              : Array.isArray(
                  data?.history
                )
                ? data.history
                : [];


        setInspections(
          records
        );

      } catch (err) {

        console.error(
          "PARAKH Dashboard Error:",
          err
        );


        setError(
          err.message ||
          "Unable to load dashboard data."
        );


        setInspections([]);

      } finally {

        setLoading(false);

      }

    };


  // ============================================================
  // STATUS NORMALIZATION
  //
  // IMPORTANT:
  // We check OVERALL STATUS first.
  // We do NOT use summary.needs_review
  // to count inspections.
  // ============================================================

  const getStatus =
    (inspection) => {

      const summary =
        inspection?.summary ||
        {};


      const compliance =
        inspection?.compliance ||
        {};


      const rawStatus =
        summary?.overall_status ??
        summary?.status ??
        compliance?.overall_status ??
        compliance?.status ??
        inspection?.overall_status ??
        inspection?.status ??
        inspection?.decision ??
        "NEEDS_REVIEW";


      const normalized =
        String(rawStatus)
          .trim()
          .toUpperCase()
          .replace(
            /[\s-]+/g,
            "_"
          );


      if (
        normalized === "PASS" ||
        normalized === "COMPLIANT"
      ) {

        return "COMPLIANT";

      }


      if (
        normalized === "FAIL" ||
        normalized === "FAILED" ||
        normalized === "NON_COMPLIANT" ||
        normalized === "NONCOMPLIANT"
      ) {

        return "NON_COMPLIANT";

      }


      if (
        normalized === "NEEDS_REVIEW" ||
        normalized === "REVIEW" ||
        normalized === "PENDING"
      ) {

        return "NEEDS_REVIEW";

      }


      return "NEEDS_REVIEW";

    };


  // ============================================================
  // PRODUCT
  // ============================================================

  const getProductName =
    (inspection) => {

      return (
        inspection?.product?.name ||
        inspection?.product?.product_name ||
        inspection?.product_name ||
        inspection?.name ||
        "Unknown Product"
      );

    };


  const getBrand =
    (inspection) => {

      return (
        inspection?.product?.brand ||
        inspection?.brand ||
        "Unknown Brand"
      );

    };


  // ============================================================
  // SCORE
  // ============================================================

  const getScore =
    (inspection) => {

      const score =
        inspection?.summary
          ?.compliance_score ??
        inspection?.summary?.score ??
        inspection?.compliance_score ??
        inspection?.compliance?.score ??
        null;


      if (
        score === null ||
        score === undefined ||
        score === ""
      ) {

        return null;

      }


      const numericScore =
        Number(score);


      if (
        Number.isNaN(
          numericScore
        )
      ) {

        return String(score);

      }


      return `${Math.round(
        numericScore
      )}%`;

    };


  // ============================================================
  // DATE
  // ============================================================

  const getDate =
    (inspection) => {

      const value =
        inspection?.created_at ||
        inspection?.timestamp ||
        inspection?.inspection_date ||
        inspection?.date;


      if (!value) {

        return "—";

      }


      const date =
        new Date(value);


      if (
        Number.isNaN(
          date.getTime()
        )
      ) {

        return String(value);

      }


      return date.toLocaleString(
        "en-IN",
        {
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }
      );

    };


  // ============================================================
  // INSPECTION ID
  // ============================================================

  const getInspectionId =
    (
      inspection,
      index
    ) => {

      return (
        inspection?.inspection_id ||
        inspection?.id ||
        `INS-${String(
          index + 1
        ).padStart(4, "0")}`
      );

    };


  // ============================================================
  // COUNTS
  //
  // These count INSPECTIONS,
  // not individual checks.
  // ============================================================

  const statistics =
    useMemo(() => {

      let compliant = 0;
      let violations = 0;
      let needsReview = 0;


      inspections.forEach(
        (inspection) => {

          const status =
            getStatus(
              inspection
            );


          if (
            status === "COMPLIANT"
          ) {

            compliant++;

          } else if (
            status === "NON_COMPLIANT"
          ) {

            violations++;

          } else {

            needsReview++;

          }

        }
      );


      const total =
        inspections.length;


      const passRate =
        total > 0
          ? Math.round(
              (compliant / total) *
              100
            )
          : 0;


      return {
        total,
        compliant,
        violations,
        needsReview,
        passRate,
      };

    }, [
      inspections,
    ]);


  // ============================================================
  // RECENT INSPECTIONS
  // ============================================================

  const recentInspections =
    inspections.slice(0, 5);


  // ============================================================
  // STATUS CLASS
  // ============================================================

  const getStatusClass =
    (status) => {

      if (
        status === "COMPLIANT"
      ) {

        return "status-compliant";

      }


      if (
        status === "NON_COMPLIANT"
      ) {

        return "status-violation";

      }


      return "status-review";

    };


  // ============================================================
  // VIEW INSPECTION
  // ============================================================

  const viewInspection =
    (inspection) => {

      navigate(
        "/inspection-details",
        {
          state: {
            inspection,
            inspectionId:
              inspection?.inspection_id ||
              inspection?.id ||
              null,
          },
        }
      );

    };


  // ============================================================
  // DONUT
  //
  // This is calculated dynamically.
  // ============================================================

  const donutStyle = {

    background:
      statistics.total === 0

        ? "conic-gradient(#e7edf5 0deg 360deg)"

        : `conic-gradient(
            #16a34a 0deg ${
              statistics.compliant /
              statistics.total *
              360
            }deg,

            #dc2626 ${
              statistics.compliant /
              statistics.total *
              360
            }deg ${
              (
                statistics.compliant +
                statistics.violations
              ) /
              statistics.total *
              360
            }deg,

            #d97706 ${
              (
                statistics.compliant +
                statistics.violations
              ) /
              statistics.total *
              360
            }deg 360deg
          )`,
  };


  // ============================================================
  // LIVE TIME / DATE DISPLAY
  // ============================================================

  const liveTime =
    currentTime.toLocaleTimeString(
      "en-IN",
      {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      }
    );


  const liveDate =
    currentTime.toLocaleDateString(
      "en-IN",
      {
        weekday: "long",
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div className="dashboard-page">


      {/* =====================================================
          HEADER
      ====================================================== */}

      <section className="dashboard-hero">

        <div className="dashboard-hero-left">

          <div className="dashboard-3d-orbit" aria-hidden="true">
            <div className="dashboard-orbit orbit-a"></div>
            <div className="dashboard-orbit orbit-b"></div>
            <div className="dashboard-orbit-core">
              <span>P</span>
            </div>
          </div>

          <div className="eyebrow">
            PARAKH INSPECTION SYSTEM
          </div>


          <h1>
            Welcome back, {userName}
          </h1>


          <p>
            Monitor packaged-product compliance
            and conduct AI-assisted inspections.
          </p>

        </div>


        {/* ==================================================
            LIVE DATE + TIME
        =================================================== */}

        <div className="dashboard-clock">

          <div className="dashboard-clock-icon">

            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
            >

              <circle
                cx="12"
                cy="12"
                r="8.5"
              />

              <path d="M12 7v5l3 2" />

            </svg>

          </div>


          <div className="dashboard-clock-content">

            <strong>
              {liveTime}
            </strong>

            <span>
              {liveDate}
            </span>

          </div>

        </div>


        {/* ==================================================
            NEW INSPECTION
        =================================================== */}

        <button
          type="button"
          className="dashboard-primary-button"
          onClick={() =>
            navigate(
              "/inspection"
            )
          }
        >

          <span>
            ＋
          </span>

          New Inspection

        </button>

      </section>


      {/* =====================================================
          STATISTICS
      ====================================================== */}

      <section className="dashboard-stats">


        {/* TOTAL */}

        <div className="dashboard-stat-card">

          <div className="stat-icon blue">
            ▣
          </div>


          <div>

            <span className="stat-label">
              Total Inspections
            </span>


            <strong>
              {loading
                ? "—"
                : statistics.total}
            </strong>


            <small>
              All recorded inspections
            </small>

          </div>

        </div>


        {/* COMPLIANT */}

        <div className="dashboard-stat-card">

          <div className="stat-icon green">
            ✓
          </div>


          <div>

            <span className="stat-label">
              Compliant
            </span>


            <strong>
              {loading
                ? "—"
                : statistics.compliant}
            </strong>


            <small>
              Passed inspections
            </small>

          </div>

        </div>


        {/* VIOLATIONS */}

        <div className="dashboard-stat-card">

          <div className="stat-icon red">
            !
          </div>


          <div>

            <span className="stat-label">
              Violations
            </span>


            <strong>
              {loading
                ? "—"
                : statistics.violations}
            </strong>


            <small>
              Non-compliant inspections
            </small>

          </div>

        </div>


        {/* REVIEW */}

        <div className="dashboard-stat-card">

          <div className="stat-icon amber">
            ?
          </div>


          <div>

            <span className="stat-label">
              Needs Review
            </span>


            <strong>
              {loading
                ? "—"
                : statistics.needsReview}
            </strong>


            <small>
              Require manual verification
            </small>

          </div>

        </div>

      </section>


      {/* =====================================================
          OVERVIEW + QUICK ACTIONS
      ====================================================== */}

      <section className="dashboard-content-grid">


        {/* ===================================================
            COMPLIANCE OVERVIEW
        ==================================================== */}

        <div className="dashboard-panel overview-panel">

          <div className="panel-heading">

            <div>

              <span className="panel-kicker">
                OVERVIEW
              </span>


              <h2>
                Compliance Overview
              </h2>

            </div>


            <span className="panel-live">
              LIVE
            </span>

          </div>


          <div className="overview-body">


            {/* DONUT */}

            <div
              className="compliance-ring"
              style={donutStyle}
            >

              <div className="ring-inner">

                <strong>
                  {loading
                    ? "—"
                    : `${statistics.passRate}%`}
                </strong>


                <span>
                  Pass Rate
                </span>

              </div>

            </div>


            {/* LEGEND */}

            <div className="overview-legend">


              <div>

                <span className="legend-dot green"></span>


                <div>

                  <strong>
                    {loading
                      ? "—"
                      : statistics.compliant}
                  </strong>


                  <small>
                    Compliant
                  </small>

                </div>

              </div>


              <div>

                <span className="legend-dot red"></span>


                <div>

                  <strong>
                    {loading
                      ? "—"
                      : statistics.violations}
                  </strong>


                  <small>
                    Violations
                  </small>

                </div>

              </div>


              <div>

                <span className="legend-dot amber"></span>


                <div>

                  <strong>
                    {loading
                      ? "—"
                      : statistics.needsReview}
                  </strong>


                  <small>
                    Needs Review
                  </small>

                </div>

              </div>

            </div>

          </div>

        </div>


        {/* ===================================================
            QUICK ACTIONS
        ==================================================== */}

        <div className="dashboard-panel quick-panel">

          <div className="panel-heading">

            <div>

              <span className="panel-kicker">
                ACTIONS
              </span>


              <h2>
                Quick Actions
              </h2>

            </div>

          </div>


          <button
            type="button"
            className="quick-action"
            onClick={() =>
              navigate(
                "/inspection"
              )
            }
          >

            <span className="quick-action-icon">
              +
            </span>


            <span>

              <strong>
                Start New Inspection
              </strong>


              <small>
                Upload and analyze a product
              </small>

            </span>


            <span className="arrow">
              →
            </span>

          </button>


          <button
            type="button"
            className="quick-action"
            onClick={() =>
              navigate(
                "/history"
              )
            }
          >

            <span className="quick-action-icon">
              ◷
            </span>


            <span>

              <strong>
                Previous Inspections
              </strong>


              <small>
                Review inspection history
              </small>

            </span>


            <span className="arrow">
              →
            </span>

          </button>

        </div>

      </section>


      {/* =====================================================
          RECENT INSPECTIONS
      ====================================================== */}

      <section className="dashboard-panel recent-panel">


        <div className="panel-heading">

          <div>

            <span className="panel-kicker">
              HISTORY
            </span>


            <h2>
              Recent Inspections
            </h2>

          </div>


          <button
            type="button"
            className="text-button"
            onClick={() =>
              navigate(
                "/history"
              )
            }
          >
            View all →
          </button>

        </div>


        {/* ===================================================
            ERROR
        ==================================================== */}

        {error && (

          <div className="error-message">
            {error}
          </div>

        )}


        {/* ===================================================
            LOADING
        ==================================================== */}

        {loading ? (

          <div className="dashboard-empty">

            <div className="loading-dot"></div>


            <p>
              Loading inspection records...
            </p>

          </div>

        ) : recentInspections.length === 0 ? (


          /* =================================================
             EMPTY
          ================================================= */

          <div className="dashboard-empty">

            <div className="empty-icon">
              +
            </div>


            <h3>
              No inspections yet
            </h3>


            <p>
              Start your first inspection to
              monitor packaged-product compliance.
            </p>


            <button
              type="button"
              className="empty-action"
              onClick={() =>
                navigate(
                  "/inspection"
                )
              }
            >
              Start Inspection
            </button>

          </div>

        ) : (


          /* =================================================
             TABLE
          ================================================= */

          <div className="recent-table">


            <div className="recent-table-header">

              <span>
                PRODUCT
              </span>


              <span>
                DATE
              </span>


              <span>
                SCORE
              </span>


              <span>
                STATUS
              </span>


              <span></span>

            </div>


            {recentInspections.map(
              (
                inspection,
                index
              ) => {

                const status =
                  getStatus(
                    inspection
                  );


                const score =
                  getScore(
                    inspection
                  );


                const inspectionId =
                  getInspectionId(
                    inspection,
                    index
                  );


                return (

                  <div
                    className="recent-row"
                    key={
                      inspectionId
                    }
                  >


                    {/* PRODUCT */}

                    <div className="recent-product">

                      <div className="product-mini-icon">
                        P
                      </div>


                      <div>

                        <strong>
                          {getProductName(
                            inspection
                          )}
                        </strong>


                        <small>
                          {getBrand(
                            inspection
                          )}
                        </small>

                      </div>

                    </div>


                    {/* DATE */}

                    <span className="recent-date">

                      {getDate(
                        inspection
                      )}

                    </span>


                    {/* SCORE */}

                    <strong className="recent-score">

                      {score ||
                        "—"}

                    </strong>


                    {/* STATUS */}

                    <span
                      className={`status-badge ${getStatusClass(
                        status
                      )}`}
                    >

                      {status.replace(
                        "_",
                        " "
                      )}

                    </span>


                    {/* VIEW */}

                    <button
                      type="button"
                      className="row-view-button"
                      onClick={() =>
                        viewInspection(
                          inspection
                        )
                      }
                    >
                      View
                    </button>

                  </div>

                );

              }
            )}

          </div>

        )}

      </section>


      {/* =====================================================
          FOOTER
      ====================================================== */}

      <div className="dashboard-footer-note">

        <span>
          ✓
        </span>


        <p>
          PARAKH provides AI-assisted OCR and
          Legal Metrology compliance analysis.
          Final enforcement decisions remain
          subject to authorized officer verification.
        </p>

      </div>

    </div>

  );

}


export default Dashboard;