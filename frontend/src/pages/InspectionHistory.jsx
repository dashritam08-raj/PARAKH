import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import "./InspectionHistory.css";
import { API_BASE_URL } from "../config/api";




function InspectionHistory() {

  const navigate = useNavigate();

  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");


  // =========================================================
  // LOAD HISTORY
  // =========================================================

  useEffect(() => {
    loadHistory();
  }, []);


  const loadHistory = async () => {

    try {

      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/history`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) {

        const data = await response
          .json()
          .catch(() => ({}));

        throw new Error(
          data?.detail ||
          "Unable to load inspection history."
        );
      }

      const data = await response.json();

      let records = [];

      if (Array.isArray(data)) {

        records = data;

      } else if (
        Array.isArray(data?.inspections)
      ) {

        records = data.inspections;

      } else if (
        Array.isArray(data?.history)
      ) {

        records = data.history;
      }

      setInspections(records);

    } catch (err) {

      console.error(
        "PARAKH History Error:",
        err
      );

      setError(
        err?.message ||
        "Unable to load inspection history."
      );

    } finally {

      setLoading(false);

    }
  };


  // =========================================================
  // HELPERS
  // =========================================================

  const getInspectionId = (
    inspection,
    index = 0
  ) => {

    return (
      inspection?.inspection_id ||
      inspection?.id ||
      `INS-${String(
        index + 1
      ).padStart(4, "0")}`
    );
  };


  const getStatus = (inspection) => {

    const inspectorDecision =
      inspection?.inspector_decision ||
      inspection?.final_decision ||
      inspection?.decision;


    if (inspectorDecision) {

      return String(
        inspectorDecision
      )
        .trim()
        .toUpperCase()
        .replace(
          /[\s-]+/g,
          "_"
        );
    }


    const summary =
      inspection?.summary || {};


    return String(

      summary?.overall_status ||

      inspection?.overall_status ||

      inspection?.status ||

      "NEEDS_REVIEW"

    )
      .trim()
      .toUpperCase()
      .replace(
        /[\s-]+/g,
        "_"
      );
  };


  const getStatusLabel = (status) => {

    switch (status) {

      case "COMPLIANT":
      case "PASS":
        return "COMPLIANT";

      case "NON_COMPLIANT":
      case "FAIL":
        return "NON-COMPLIANT";

      case "NEEDS_REVIEW":
      case "REVIEW":
        return "NEEDS REVIEW";

      default:
        return "PENDING";
    }
  };


  const getStatusClass = (status) => {

    switch (status) {

      case "COMPLIANT":
      case "PASS":
        return "compliant";

      case "NON_COMPLIANT":
      case "FAIL":
        return "non-compliant";

      case "NEEDS_REVIEW":
      case "REVIEW":
        return "review";

      default:
        return "pending";
    }
  };


  const getProductName = (inspection) => {

    return (
      inspection?.product?.name ||
      inspection?.product?.product_name ||
      inspection?.product_name ||
      "Unknown Product"
    );
  };


  const getBrand = (inspection) => {

    return (
      inspection?.product?.brand ||
      inspection?.brand ||
      "—"
    );
  };


  const getScore = (inspection) => {

    const score =
      inspection?.summary?.compliance_score ??
      inspection?.summary?.score ??
      inspection?.compliance_score ??
      inspection?.compliance?.score ??
      null;


    if (
      score === null ||
      score === undefined ||
      score === ""
    ) {

      return "—";
    }


    const number = Number(score);


    if (Number.isNaN(number)) {

      return String(score);
    }


    return `${Math.round(number)}%`;
  };


  const getDate = (inspection) => {

    const value =
      inspection?.created_at ||
      inspection?.timestamp ||
      inspection?.inspection_date ||
      inspection?.date;


    if (!value) {

      return "—";
    }


    const date = new Date(value);


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


  const getInspectorName = (inspection) => {

    return (
      inspection?.inspector_name ||
      inspection?.final_inspector ||
      ""
    );
  };


  // =========================================================
  // COUNTS
  // =========================================================

  const counts = useMemo(() => {

    let compliant = 0;
    let violations = 0;
    let review = 0;


    inspections.forEach(
      (inspection) => {

        const status =
          getStatus(inspection);


        if (
          status === "COMPLIANT" ||
          status === "PASS"
        ) {

          compliant++;

        } else if (
          status === "NON_COMPLIANT" ||
          status === "FAIL"
        ) {

          violations++;

        } else {

          review++;
        }
      }
    );


    return {
      total: inspections.length,
      compliant,
      violations,
      review,
    };

  }, [inspections]);


  // =========================================================
  // SEARCH + FILTER
  // =========================================================

  const filteredInspections = useMemo(() => {

    const query =
      search
        .trim()
        .toLowerCase();


    return inspections.filter(
      (inspection) => {

        const status =
          getStatus(inspection);


        let statusMatches = true;


        if (
          statusFilter ===
          "COMPLIANT"
        ) {

          statusMatches =
            status === "COMPLIANT" ||
            status === "PASS";
        }


        if (
          statusFilter ===
          "NON_COMPLIANT"
        ) {

          statusMatches =
            status === "NON_COMPLIANT" ||
            status === "FAIL";
        }


        if (
          statusFilter ===
          "NEEDS_REVIEW"
        ) {

          statusMatches =
            status === "NEEDS_REVIEW" ||
            status === "REVIEW";
        }


        const searchableText = [

          inspection?.inspection_id,

          inspection?.id,

          getProductName(
            inspection
          ),

          getBrand(
            inspection
          ),

          status,

        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();


        const searchMatches =
          !query ||
          searchableText.includes(
            query
          );


        return (
          statusMatches &&
          searchMatches
        );
      }
    );

  }, [
    inspections,
    search,
    statusFilter,
  ]);


  // =========================================================
  // VIEW
  // =========================================================

  const handleView = (inspection) => {

    const inspectionId =
      inspection?.inspection_id ||
      inspection?.id;


    if (!inspectionId) {

      setError(
        "This inspection does not have a valid ID."
      );

      return;
    }


    navigate(
      "/inspection-details",
      {
        state: {
          inspection,
          inspectionId,
        },
      }
    );
  };


  // =========================================================
  // DELETE
  // =========================================================

  const handleDelete = async (
    inspection
  ) => {

    const inspectionId =
      inspection?.inspection_id ||
      inspection?.id;


    if (!inspectionId) {
      return;
    }


    const confirmed =
      window.confirm(
        "Delete this inspection permanently?"
      );


    if (!confirmed) {
      return;
    }


    try {

      const response =
        await fetch(
          `${API_BASE_URL}/history/${inspectionId}`,
          {
            method: "DELETE",
            credentials: "include",
          }
        );


      if (!response.ok) {

        const data =
          await response
            .json()
            .catch(() => ({}));


        throw new Error(
          data?.detail ||
          "Unable to delete inspection."
        );
      }


      setInspections(
        (previous) =>
          previous.filter(
            (item) =>
              (
                item?.inspection_id ||
                item?.id
              ) !== inspectionId
          )
      );


    } catch (err) {

      console.error(
        "Delete error:",
        err
      );


      window.alert(
        err?.message ||
        "Unable to delete inspection."
      );
    }
  };


  // =========================================================
  // PAGE
  // =========================================================

  return (

    <div className="history-page">

      {/* HEADER */}

      <header className="history-header">

        <div>

          <span className="history-eyebrow">
            INSPECTION RECORDS
          </span>

          <h1>
            Inspection History
          </h1>

          <p>
            Review previous inspections and
            final Inspector decisions.
          </p>

        </div>


        <div className="history-header-actions">

          <button
            type="button"
            className="history-refresh-button"
            onClick={loadHistory}
            disabled={loading}
          >
            ↻
            <span>
              {loading
                ? "Refreshing..."
                : "Refresh"}
            </span>
          </button>


          <button
            type="button"
            className="history-new-button"
            onClick={() =>
              navigate("/inspection")
            }
          >
            +
            <span>
              New Inspection
            </span>
          </button>

        </div>

      </header>


      {/* STATS */}

      <section className="history-stats">

        <div className="history-stat">

          <span className="history-stat-icon blue">
            #
          </span>

          <div>
            <small>
              TOTAL INSPECTIONS
            </small>

            <strong>
              {counts.total}
            </strong>
          </div>

        </div>


        <div className="history-stat">

          <span className="history-stat-icon green">
            ✓
          </span>

          <div>
            <small>
              COMPLIANT
            </small>

            <strong>
              {counts.compliant}
            </strong>
          </div>

        </div>


        <div className="history-stat">

          <span className="history-stat-icon red">
            !
          </span>

          <div>
            <small>
              NON-COMPLIANT
            </small>

            <strong>
              {counts.violations}
            </strong>
          </div>

        </div>


        <div className="history-stat">

          <span className="history-stat-icon amber">
            ?
          </span>

          <div>
            <small>
              NEEDS REVIEW
            </small>

            <strong>
              {counts.review}
            </strong>
          </div>

        </div>

      </section>


      {/* TOOLBAR */}

      <section className="history-toolbar">

        <div className="history-search">

          <span>
            ⌕
          </span>

          <input
            type="text"
            placeholder="Search product, brand or inspection ID..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
          />

        </div>


        <div className="history-filters">

          {[
            ["ALL", "All"],
            ["COMPLIANT", "Compliant"],
            [
              "NON_COMPLIANT",
              "Non-Compliant",
            ],
            [
              "NEEDS_REVIEW",
              "Needs Review",
            ],
          ].map(
            ([value, label]) => (

              <button
                key={value}
                type="button"
                className={
                  statusFilter === value
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setStatusFilter(
                    value
                  )
                }
              >
                {label}
              </button>

            )
          )}

        </div>

      </section>


      {/* ERROR */}

      {error && (

        <div className="history-error">

          <strong>
            Unable to load history
          </strong>

          <span>
            {error}
          </span>

          <button
            type="button"
            onClick={loadHistory}
          >
            Try Again
          </button>

        </div>

      )}


      {/* LOADING */}

      {loading ? (

        <div className="history-loading">

          <div className="history-spinner" />

          <h3>
            Loading inspection records...
          </h3>

          <p>
            Retrieving data from PARAKH.
          </p>

        </div>

      ) : filteredInspections.length === 0 ? (

        <div className="history-empty">

          <div className="history-empty-icon">
            ◷
          </div>

          <h2>
            {inspections.length === 0
              ? "No inspections yet"
              : "No matching inspections"}
          </h2>

          <p>
            {inspections.length === 0
              ? "Run your first product inspection and it will appear here."
              : "Try changing your search or status filter."}
          </p>


          {inspections.length === 0 && (

            <button
              type="button"
              onClick={() =>
                navigate(
                  "/inspection"
                )
              }
            >
              Start New Inspection
            </button>

          )}

        </div>

      ) : (

        <section className="history-table-card">

          <div className="history-table-heading">

            <div>

              <span>
                RECORDS
              </span>

              <h2>
                Previous Inspections
              </h2>

            </div>

            <small>
              {filteredInspections.length} record
              {filteredInspections.length !== 1
                ? "s"
                : ""}
            </small>

          </div>


          <div className="history-table-scroll">

            <table>

              <thead>

                <tr>

                  <th>
                    INSPECTION
                  </th>

                  <th>
                    PRODUCT
                  </th>

                  <th>
                    BRAND
                  </th>

                  <th>
                    DATE
                  </th>

                  <th>
                    SCORE
                  </th>

                  <th>
                    STATUS
                  </th>

                  <th>
                    ACTIONS
                  </th>

                </tr>

              </thead>


              <tbody>

                {filteredInspections.map(
                  (
                    inspection,
                    index
                  ) => {

                    const inspectionId =
                      getInspectionId(
                        inspection,
                        index
                      );

                    const status =
                      getStatus(
                        inspection
                      );

                    const inspectorName =
                      getInspectorName(
                        inspection
                      );


                    return (

                      <tr
                        key={
                          inspectionId
                        }
                      >

                        <td>

                          <div className="history-id-cell">

                            <strong>
                              {inspectionId}
                            </strong>

                            <span>
                              {inspection?.filename ||
                                "Product image"}
                            </span>

                          </div>

                        </td>


                        <td>

                          <strong className="history-product-name">
                            {getProductName(
                              inspection
                            )}
                          </strong>

                        </td>


                        <td>
                          {getBrand(
                            inspection
                          )}
                        </td>


                        <td>

                          <span className="history-date">
                            {getDate(
                              inspection
                            )}
                          </span>

                        </td>


                        <td>

                          <strong className="history-score">
                            {getScore(
                              inspection
                            )}
                          </strong>

                        </td>


                        <td>

                          <div className="history-status-cell">

                            <span
                              className={`history-status ${getStatusClass(
                                status
                              )}`}
                            >
                              {getStatusLabel(
                                status
                              )}
                            </span>


                            {inspectorName && (

                              <small>
                                Inspector verified
                              </small>

                            )}

                          </div>

                        </td>


                        <td>

                          <div className="history-actions">

                            <button
                              type="button"
                              className="history-view"
                              onClick={() =>
                                handleView(
                                  inspection
                                )
                              }
                            >
                              View
                            </button>


                            <button
                              type="button"
                              className="history-delete"
                              onClick={() =>
                                handleDelete(
                                  inspection
                                )
                              }
                            >
                              Delete
                            </button>

                          </div>

                        </td>

                      </tr>

                    );

                  }
                )}

              </tbody>

            </table>

          </div>

        </section>

      )}

    </div>

  );
}


export default InspectionHistory;