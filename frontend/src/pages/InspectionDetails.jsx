import {
  useEffect,
  useState,
} from "react";

import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import { API_BASE_URL } from "../config/api";


function InspectionDetails() {

  const location =
    useLocation();

  const navigate =
    useNavigate();


  const passedInspection =
    location.state?.inspection ||
    null;


  const passedInspectionId =
    location.state?.inspectionId ||
    passedInspection?.inspection_id ||
    passedInspection?.id ||
    null;


  const [inspection, setInspection] =
    useState(passedInspection);


  const [loading, setLoading] =
    useState(!passedInspection);


  const [error, setError] =
    useState("");


  const [generatingReport, setGeneratingReport] =
    useState(false);

  const [inspectorRemarks, setInspectorRemarks] =
    useState(
      passedInspection?.inspector_remarks ||
      passedInspection?.remarks ||
      passedInspection?.final_remarks ||
      ""
    );

  const [savingDecision, setSavingDecision] =
    useState(false);

  const [decisionSaved, setDecisionSaved] =
    useState(
      Boolean(
        passedInspection?.inspector_decision ||
        passedInspection?.final_decision ||
        passedInspection?.decision
      )
    );


  /* =========================================================
     LOAD DETAILS
  ========================================================= */

  useEffect(() => {

    if (passedInspection) {
      setInspection(
        passedInspection
      );

      setLoading(false);

      return;
    }


    if (!passedInspectionId) {

      setLoading(false);

      setError(
        "No inspection was selected."
      );

      return;

    }


    loadInspection(
      passedInspectionId
    );

  }, [
    passedInspection,
    passedInspectionId,
  ]);


  const loadInspection = async (
    inspectionId
  ) => {

    setLoading(true);
    setError("");

    try {

      const response =
        await fetch(
          `${API_BASE_URL}/history/${inspectionId}`,
          {
            credentials: "include",
          }
        );


      if (!response.ok) {

        const data =
          await response.json()
            .catch(() => ({}));


        throw new Error(
          data.detail ||
          "Unable to load inspection details."
        );

      }


      const data =
        await response.json();


      setInspection(
        data?.inspection || data
      );

    } catch (err) {

      console.error(
        "Inspection details error:",
        err
      );

      setError(
        err.message ||
        "Unable to load inspection."
      );

    } finally {

      setLoading(false);

    }

  };


  /* =========================================================
     HELPERS
  ========================================================= */

  const getStatus = () => {
    const inspectorDecision =
      inspection?.inspector_decision ||
      inspection?.final_decision ||
      inspection?.decision;

    if (inspectorDecision) {
      return String(inspectorDecision).toUpperCase();
    }

    return String(
      inspection?.summary?.overall_status ??
      inspection?.overall_status ??
      inspection?.status ??
      "NEEDS_REVIEW"
    ).toUpperCase();
  };


  const getProduct = () => {

    return (
      inspection?.product ||
      {}
    );

  };


  const product =
    getProduct();


  const summary =
    inspection?.summary ||
    {};


  const checks =
    inspection?.compliance_checks ||
    inspection?.checks ||
    inspection?.compliance?.checks ||
    [];


  const score =
    summary?.compliance_score ??
    summary?.score ??
    inspection?.compliance_score ??
    inspection?.compliance?.score;


  const status =
    getStatus();


  const getStatusClass = () => {

    if (
      status === "COMPLIANT" ||
      status === "PASS"
    ) {
      return "pass";
    }


    if (
      status === "NON_COMPLIANT" ||
      status === "FAIL"
    ) {
      return "fail";
    }


    if (
      status === "NEEDS_REVIEW" ||
      status === "REVIEW"
    ) {
      return "review";
    }


    return "pending";

  };


  const formatDate = (
    value
  ) => {

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
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    );

  };


  /* =========================================================
     INSPECTOR FINAL DECISION
  ========================================================= */

  const saveInspectorDecision = async (decision) => {
    const inspectionId =
      inspection?.inspection_id ||
      inspection?.id ||
      passedInspectionId;

    if (!inspectionId) {
      setError("Inspection ID is missing.");
      return;
    }

    if (
      decision === "NON_COMPLIANT" &&
      !inspectorRemarks.trim()
    ) {
      setError(
        "Inspector remarks are required when marking this inspection non-compliant."
      );
      return;
    }

    const confirmed = window.confirm(
      decision === "COMPLIANT"
        ? "Confirm: Mark this inspection as COMPLIANT?"
        : "Confirm: Mark this inspection as NON-COMPLIANT?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setSavingDecision(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/history/${inspectionId}/decision`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            decision,
            inspector_name: "PARAKH Inspector",
            remarks: inspectorRemarks.trim(),
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          "Unable to save Inspector decision."
        );
      }

      const updatedInspection =
        data?.inspection || data;

      setInspection(updatedInspection);

      setInspectorRemarks(
        updatedInspection?.inspector_remarks ||
        updatedInspection?.remarks ||
        inspectorRemarks
      );

      setDecisionSaved(true);

    } catch (err) {
      console.error(
        "Inspector decision error:",
        err
      );

      setError(
        err.message ||
        "Unable to save Inspector decision."
      );

    } finally {
      setSavingDecision(false);
    }
  };

  /* =========================================================
     REPORT
  ========================================================= */

  const downloadReport = async () => {
    setGeneratingReport(true);
    setError("");

    try {
      // The current backend /generate-report endpoint expects
      // multipart/form-data with the original product image.
      // A saved history record does not contain that uploaded File object.
      //
      // Therefore, do not send JSON to this endpoint.
      // If the original image is available in this browser session,
      // Inspection.jsx should generate the report there.

      throw new Error(
        "PDF regeneration from a saved history record requires the original product image. Use Generate Report from the inspection result."
      );

    } catch (err) {
      console.error(
        "Report download error:",
        err
      );

      setError(
        err.message ||
        "Unable to generate the PDF report."
      );

    } finally {
      setGeneratingReport(false);
    }
  };


  /* =========================================================
     LOADING
  ========================================================= */

  if (loading) {

    return (
      <div className="details-page">

        <div className="details-loading">

          <div className="loading-dot"></div>

          <h2>
            Loading Inspection
          </h2>

          <p>
            Fetching the complete inspection record...
          </p>

        </div>

      </div>
    );

  }


  /* =========================================================
     ERROR
  ========================================================= */

  if (
    error &&
    !inspection
  ) {

    return (
      <div className="details-page">

        <div className="details-empty">

          <div className="empty-icon">
            !
          </div>

          <h2>
            Inspection not found
          </h2>

          <p>
            {error}
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={() =>
              navigate("/history")
            }
          >
            Back to History
          </button>

        </div>

      </div>
    );

  }


  return (
    <div className="details-page">


      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="details-page-header">

        <div>

          <button
            type="button"
            className="back-button"
            onClick={() =>
              navigate("/history")
            }
          >
            ← Back to History
          </button>


          <div className="eyebrow">
            INSPECTION DETAILS
          </div>

          <h1>
            {product?.name ||
              product?.product_name ||
              inspection?.product_name ||
              "Inspection Record"}
          </h1>

          <p>
            Complete AI-assisted compliance
            analysis and inspection evidence.
          </p>

        </div>


        <div className="details-header-actions">

          <span
            className={`status-badge ${getStatusClass()}`}
          >
            {status.replace(
              "_",
              " "
            )}
          </span>

        </div>

      </div>


      {/* =====================================================
          SUMMARY
      ===================================================== */}

      <div className="details-summary-grid">

        <div className="details-summary-card">

          <span>
            Compliance Score
          </span>

          <strong>
            {score !== null &&
            score !== undefined
              ? `${score}%`
              : "—"}
          </strong>

        </div>


        <div className="details-summary-card">

          <span>
            Passed Checks
          </span>

          <strong>
            {summary?.passed ??
              "—"}
          </strong>

        </div>


        <div className="details-summary-card">

          <span>
            Failed Checks
          </span>

          <strong>
            {summary?.failed ??
              "—"}
          </strong>

        </div>


        <div className="details-summary-card">

          <span>
            Needs Review
          </span>

          <strong>
            {summary?.needs_review ??
              "—"}
          </strong>

        </div>

      </div>


      {/* =====================================================
          PRODUCT INFORMATION
      ===================================================== */}

      <section className="details-card">

        <div className="details-card-heading">

          <div>

            <span className="panel-kicker">
              PRODUCT
            </span>

            <h2>
              Product Information
            </h2>

          </div>

        </div>


        <div className="details-info-grid">

          <div>
            <span>
              Product Name
            </span>

            <strong>
              {product?.name ||
                product?.product_name ||
                inspection?.product_name ||
                "Not detected"}
            </strong>
          </div>


          <div>
            <span>
              Brand
            </span>

            <strong>
              {product?.brand ||
                inspection?.brand ||
                "Not detected"}
            </strong>
          </div>


          <div>
            <span>
              Net Quantity
            </span>

            <strong>
              {product?.net_quantity ||
                product?.quantity ||
                "Not detected"}
            </strong>
          </div>


          <div>
            <span>
              MRP
            </span>

            <strong>
              {product?.mrp ||
                inspection?.mrp ||
                "Not detected"}
            </strong>
          </div>


          <div>
            <span>
              Manufacturer
            </span>

            <strong>
              {product?.manufacturer ||
                inspection?.manufacturer ||
                "Not detected"}
            </strong>
          </div>


          <div>
            <span>
              Inspection Date
            </span>

            <strong>
              {formatDate(
                inspection?.created_at ||
                inspection?.timestamp ||
                inspection?.inspection_date
              )}
            </strong>
          </div>

        </div>

      </section>


      {/* =====================================================
          COMPLIANCE CHECKS
      ===================================================== */}

      <section className="details-card">

        <div className="details-card-heading">

          <div>

            <span className="panel-kicker">
              LEGAL METROLOGY
            </span>

            <h2>
              Compliance Checks
            </h2>

          </div>

          <span className="rule-chip">
            Packaged Commodities Rules
          </span>

        </div>


        {Array.isArray(checks) &&
        checks.length > 0 ? (

          <div className="details-check-list">

            {checks.map(
              (check, index) => {

                const checkStatus =
                  String(
                    check?.status ||
                    check?.result ||
                    check?.compliance_status ||
                    "NEEDS_REVIEW"
                  ).toUpperCase();


                const passed =
                  checkStatus === "PASS" ||
                  checkStatus === "COMPLIANT";


                const failed =
                  checkStatus === "FAIL" ||
                  checkStatus === "NON_COMPLIANT";


                return (
                  <div
                    className={`details-check ${
                      passed
                        ? "check-pass"
                        : failed
                          ? "check-fail"
                          : "check-review"
                    }`}
                    key={index}
                  >

                    <div className="check-symbol">

                      {passed
                        ? "✓"
                        : failed
                          ? "×"
                          : "!"}

                    </div>


                    <div className="check-body">

                      <div className="check-title">

                        <strong>
                          {check?.name ||
                            check?.rule ||
                            check?.title ||
                            `Compliance Check ${
                              index + 1
                            }`}
                        </strong>

                        <span>
                          {checkStatus.replace(
                            "_",
                            " "
                          )}
                        </span>

                      </div>


                      <p>
                        {check?.message ||
                          check?.description ||
                          check?.reason ||
                          "No additional explanation provided."}
                      </p>


                      {(check?.evidence ||
                        check?.ocr_evidence) && (

                        <div className="check-evidence">

                          <strong>
                            Evidence
                          </strong>

                          <span>
                            {check?.evidence ||
                              check?.ocr_evidence}
                          </span>

                        </div>

                      )}

                    </div>

                  </div>
                );

              }
            )}

          </div>

        ) : (

          <div className="details-no-checks">

            <span>
              !
            </span>

            <div>

              <strong>
                Compliance check details unavailable
              </strong>

              <p>
                The saved inspection does not
                contain individual check records.
              </p>

            </div>

          </div>

        )}

      </section>


      {/* =====================================================
          OCR EVIDENCE
      ===================================================== */}

      <section className="details-card">

        <div className="details-card-heading">

          <div>

            <span className="panel-kicker">
              EVIDENCE
            </span>

            <h2>
              OCR Evidence
            </h2>

          </div>

        </div>


        <details className="details-ocr">

          <summary>
            View extracted package text
          </summary>

          <pre>
            {inspection?.ocr_text ||
              "No OCR text available."}
          </pre>

        </details>

      </section>


      {/* =====================================================
          INSPECTOR FINAL DECISION
      ===================================================== */}

      <section className="details-card inspector-decision-card">

        <div className="details-card-heading">

          <div>
            <span className="panel-kicker">
              FINAL VERIFICATION
            </span>

            <h2>
              Inspector Decision
            </h2>

            <p>
              Review the AI findings and record the final inspection decision.
            </p>
          </div>

          <span
            className={`status-badge ${getStatusClass()}`}
          >
            {status.replace(/_/g, " ")}
          </span>

        </div>

        {decisionSaved && (
          <div className="decision-success">
            <strong>✓ Decision saved successfully</strong>
            <span>
              The final Inspector decision has been added to this inspection record.
            </span>
          </div>
        )}

        <div className="inspector-remarks">

          <label htmlFor="details-inspector-remarks">
            Inspector Remarks
          </label>

          <textarea
            id="details-inspector-remarks"
            value={inspectorRemarks}
            onChange={(event) =>
              setInspectorRemarks(event.target.value)
            }
            placeholder="Enter observations, evidence notes or reason for the final decision..."
            rows={4}
            disabled={savingDecision}
          />

        </div>

        <div className="decision-buttons">

          <button
            type="button"
            className="decision-button decision-compliant"
            disabled={savingDecision}
            onClick={() =>
              saveInspectorDecision("COMPLIANT")
            }
          >
            <span className="decision-button-icon">
              ✓
            </span>

            <span>
              <strong>
                {savingDecision
                  ? "Saving..."
                  : "Mark Compliant"}
              </strong>

              <small>
                Confirm that the reviewed package meets the requirements.
              </small>
            </span>
          </button>

          <button
            type="button"
            className="decision-button decision-non-compliant"
            disabled={savingDecision}
            onClick={() =>
              saveInspectorDecision("NON_COMPLIANT")
            }
          >
            <span className="decision-button-icon">
              !
            </span>

            <span>
              <strong>
                {savingDecision
                  ? "Saving..."
                  : "Mark Non-Compliant"}
              </strong>

              <small>
                Record a violation after reviewing the evidence.
              </small>
            </span>
          </button>

        </div>

        {(inspection?.inspector_decision ||
          inspection?.final_decision ||
          inspection?.decision) && (
          <div className="saved-decision-meta">

            <span>
              Final decision:
            </span>

            <strong>
              {String(
                inspection?.inspector_decision ||
                inspection?.final_decision ||
                inspection?.decision
              ).replace(/_/g, " ")}
            </strong>

            {(inspection?.inspector_name ||
              inspection?.final_inspector) && (
              <span>
                by{" "}
                {inspection?.inspector_name ||
                  inspection?.final_inspector}
              </span>
            )}

          </div>
        )}

      </section>


      {/* =====================================================
          REPORT / ACTIONS
      ===================================================== */}

      <section className="details-action-card">

        <div>

          <span className="panel-kicker">
            REPORT
          </span>

          <h2>
            Inspection Report
          </h2>

          <p>
            Generate a formal PDF report containing
            the inspection findings and evidence.
          </p>

        </div>


        <button
          type="button"
          className="report-button"
          disabled={generatingReport}
          onClick={downloadReport}
        >
          {generatingReport
            ? "Generating PDF..."
            : "Download PDF Report"}
        </button>

      </section>


      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

    </div>
  );
}


export default InspectionDetails;