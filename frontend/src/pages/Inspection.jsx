import { useEffect, useRef, useState } from "react";
import "./Inspection.css";
import CameraCapture from "../components/CameraCapture";

import { API_BASE_URL } from "../config/api";

function Inspection() {
  const [image, setImage] = useState(null);
  const [file, setFile] = useState(null);

  const [analyzing, setAnalyzing] = useState(false);
  const [generatingReport, setGeneratingReport] =
    useState(false);

  const [inspectorRemarks, setInspectorRemarks] =
    useState("");

  const [savingDecision, setSavingDecision] =
    useState(false);

  const [decisionSaved, setDecisionSaved] =
    useState(false);

  const [analysisStage, setAnalysisStage] =
    useState(0);

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [showCamera, setShowCamera] = useState(false);
  const [isMobileDevice, setIsMobileDevice] = useState(false);
  const [processingImage, setProcessingImage] = useState(false);
  const cameraInputRef = useRef(null);

  // ============================================================
  // DEVICE DETECTION
  // ============================================================

  useEffect(() => {
    const mobile =
      /Android|iPhone|iPad|iPod|Mobile/i.test(
        navigator.userAgent
      );

    setIsMobileDevice(mobile);
  }, []);

  // ============================================================
  // CLEANUP IMAGE URL
  // ============================================================

  useEffect(() => {
    return () => {
      if (image) {
        URL.revokeObjectURL(image);
      }
    };
  }, [image]);

  // ============================================================
  // IMAGE SELECTION
  // ============================================================

  const handleImageChange = async (event) => {
    const selectedFile = event.target.files?.[0];

    event.target.value = "";

    if (!selectedFile) return;

    const allowedTypes = [
      "image/png",
      "image/jpeg",
      "image/jpg",
      "image/webp",
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError(
        "Please select a PNG, JPG, JPEG or WebP image."
      );
      return;
    }

    const maxOriginalSize = 12 * 1024 * 1024;

    if (selectedFile.size > maxOriginalSize) {
      setError(
        "This camera image is too large. Please capture the product at a lower resolution."
      );
      return;
    }

    try {
      setProcessingImage(true);
      setError("");

      /*
       * COMPUTER UPLOAD FIX
       * --------------------
       * Do not force a desktop-selected image through the browser's
       * Image/FileReader decoder before showing it.
       *
       * Windows can provide perfectly valid JPG/PNG files that a browser
       * canvas decoder may temporarily fail to decode. The browser can still
       * preview and upload the original File directly.
       *
       * The backend receives the original image, so this avoids the
       * misleading "Could not decode the captured image" error.
       */
      setCapturedImage(selectedFile);
    } catch (err) {
      console.error(
        "PARAKH IMAGE UPLOAD ERROR:",
        err
      );

      setError(
        err?.message ||
          "Unable to load the selected image. Please try another JPG or PNG file."
      );
    } finally {
      setProcessingImage(false);
    }
  };

  // ============================================================
  // CAMERA CAPTURE
  // ============================================================

  const openCamera = () => {
    setError("");

    if (isMobileDevice) {
      // Phone/tablet → native device camera
      cameraInputRef.current?.click();
    } else {
      // Laptop/desktop → live webcam modal
      setShowCamera(true);
    }
  };

  const closeCamera = () => {
    setShowCamera(false);
  };

  const compressImage = (
    inputFile,
    maxWidth = 1280,
    quality = 0.72
  ) => {
    return new Promise((resolve, reject) => {
      if (!inputFile) {
        reject(new Error("No image was selected."));
        return;
      }

      // Some phone cameras return a Blob/File whose temporary object URL
      // cannot be decoded reliably by every browser. Reading the file as a
      // data URL is more compatible with Android/iOS camera captures.
      const reader = new FileReader();
      const img = new Image();

      let finished = false;

      const fail = (message) => {
        if (finished) return;
        finished = true;

        reader.onload = null;
        reader.onerror = null;
        img.onload = null;
        img.onerror = null;
        img.src = "";

        reject(new Error(message));
      };

      reader.onerror = () => {
        fail("Could not read the selected image file.");
      };

      reader.onload = () => {
        if (finished) return;

        const dataUrl = reader.result;

        if (
          typeof dataUrl !== "string" ||
          !dataUrl.startsWith("data:image/")
        ) {
          fail(
            "The selected file is not a readable image. Please use JPG, PNG or WebP."
          );
          return;
        }

        img.onload = () => {
          if (finished) return;

          try {
            let width = img.naturalWidth;
            let height = img.naturalHeight;

            if (!width || !height) {
              fail("Invalid image dimensions.");
              return;
            }

            if (width > maxWidth) {
              height = Math.round(
                (height * maxWidth) / width
              );
              width = maxWidth;
            }

            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;

            const ctx = canvas.getContext("2d", {
              alpha: false
            });

            if (!ctx) {
              fail("Could not create image canvas.");
              return;
            }

            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = "high";
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, width, height);
            ctx.drawImage(img, 0, 0, width, height);

            // Release decoded image memory before JPEG encoding.
            img.src = "";

            canvas.toBlob(
              (blob) => {
                // Release canvas backing memory immediately.
                canvas.width = 1;
                canvas.height = 1;

                if (finished) return;

                if (!blob) {
                  fail("Image compression failed.");
                  return;
                }

                finished = true;

                reader.onload = null;
                reader.onerror = null;
                img.onload = null;
                img.onerror = null;

                resolve(
                  new File(
                    [blob],
                    "parakh-inspection.jpg",
                    {
                      type: "image/jpeg",
                      lastModified: Date.now()
                    }
                  )
                );
              },
              "image/jpeg",
              quality
            );
          } catch (error) {
            fail(
              error?.message ||
                "Unable to process the image."
            );
          }
        };

        img.onerror = () => {
          fail(
            "Could not decode the captured image. Please capture the package again in JPG/PNG format."
          );
        };

        img.src = dataUrl;
      };

      reader.readAsDataURL(inputFile);
    });
  };

  const setCapturedImage = (capturedFile) => {
    if (!capturedFile) return;

    const allowedTypes = [
      "image/png",
      "image/jpeg",
      "image/jpg",
      "image/webp",
    ];

    if (!allowedTypes.includes(capturedFile.type)) {
      setError(
        "Please capture a PNG, JPG, JPEG or WebP image."
      );
      return;
    }

    // Final safety limit after compression.
    const maxSize = 4 * 1024 * 1024;

    if (capturedFile.size > maxSize) {
      setError(
        "Processed image is still too large. Please capture the product again."
      );
      return;
    }

    if (image) {
      URL.revokeObjectURL(image);
    }

    setFile(capturedFile);
    setImage(URL.createObjectURL(capturedFile));
    setResult(null);
    setInspectorRemarks("");
    setDecisionSaved(false);
    setError("");
    setAnalysisStage(0);
  };

  const handleCameraCapture = async (capturedFile) => {
    if (!capturedFile) return;

    try {
      setProcessingImage(true);
      setError("");

      const compressedFile =
        await compressImage(capturedFile);

      setCapturedImage(compressedFile);
      setShowCamera(false);
    } catch (err) {
      console.error(
        "PARAKH CAMERA PROCESSING ERROR:",
        err
      );

      setError(
        err?.message ||
          "Unable to process the captured image. Please try again."
      );
      setShowCamera(false);
    } finally {
      setProcessingImage(false);
    }
  };

  const handleCameraImage = async (event) => {
    const capturedFile =
      event.target.files?.[0];
    console.log("PHONE CAMERA FILE:", capturedFile);
    console.log("TYPE:", capturedFile?.type);
    console.log("SIZE:", capturedFile?.size);

    event.target.value = "";

    if (!capturedFile) return;

    try {
      setProcessingImage(true);
      setError("");

      const compressedFile =
        await compressImage(capturedFile);

      setCapturedImage(compressedFile);
    } catch (err) {
      console.error(
        "PARAKH PHONE CAMERA ERROR:",
        err
      );

      setError(
        err?.message ||
          "Unable to process the captured image. Please try again."
      );
    } finally {
      setProcessingImage(false);
    }
  };

  // ============================================================
  // ANALYZE PRODUCT
  // ============================================================

  const analyzeProduct = async () => {
    if (!file) {
      setError(
        "Please upload a product image first."
      );
      return;
    }

    if (processingImage) {
      setError(
        "Please wait while the image is being prepared."
      );
      return;
    }

    if (analyzing) {
      return;
    }

    setAnalyzing(true);
    setResult(null);
    setError("");
    setDecisionSaved(false);
    setAnalysisStage(1);

    // ----------------------------------------------------------
    // VISUAL ANALYSIS STAGES
    // ----------------------------------------------------------

    const stageTimer1 =
      setTimeout(() => {
        setAnalysisStage(2);
      }, 900);

    const stageTimer2 =
      setTimeout(() => {
        setAnalysisStage(3);
      }, 2200);

    const stageTimer3 =
      setTimeout(() => {
        setAnalysisStage(4);
      }, 4000);

    const formData =
      new FormData();

    formData.append(
      "file",
      file
    );

    try {
      // --------------------------------------------------------
      // API REQUEST
      // --------------------------------------------------------

      const response =
        await fetch(
          `${API_BASE_URL}/analyze`,
          {
            method: "POST",
            body: formData,
            credentials: "include",
          }
        );

      // --------------------------------------------------------
      // PARSE RESPONSE
      // --------------------------------------------------------

      let data = null;

      try {
        data =
          await response.json();
      } catch {
        data = null;
      }

      // --------------------------------------------------------
      // HANDLE API ERROR
      // --------------------------------------------------------

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            `Server returned ${response.status}`
        );
      }

      // --------------------------------------------------------
      // FINAL ANALYSIS STAGE
      // --------------------------------------------------------

      setAnalysisStage(4);

      console.log(
        "PARAKH ANALYSIS RESULT:",
        data
      );

      // --------------------------------------------------------
      // SAVE RESULT
      // --------------------------------------------------------

      setResult(data);

    } catch (err) {
      console.error(
        "PARAKH ANALYSIS ERROR:",
        err
      );

      setError(
        err?.message ||
          "Unable to analyze the product. Please make sure the PARAKH backend is running and reachable on the configured network."
      );

      setAnalysisStage(0);

    } finally {
      clearTimeout(
        stageTimer1
      );

      clearTimeout(
        stageTimer2
      );

      clearTimeout(
        stageTimer3
      );

      setAnalyzing(false);
    }
  };

  // ============================================================
  // GENERATE PDF REPORT
  // ============================================================

  const generateReport = async () => {
    if (!file) {
      setError(
        "Please upload a product image first."
      );
      return;
    }

    if (!result) {
      setError(
        "Please analyze the product before generating the PDF report."
      );
      return;
    }

    if (generatingReport) {
      return;
    }

    setGeneratingReport(true);
    setError("");

    const formData =
      new FormData();

    // ----------------------------------------------------------
    // ORIGINAL IMAGE
    // ----------------------------------------------------------

    formData.append(
      "file",
      file
    );

    // ----------------------------------------------------------
    // COMPLETE ANALYSIS RESULT
    // ----------------------------------------------------------

    formData.append(
      "analysis_result",
      JSON.stringify(result)
    );

    try {
      const response =
        await fetch(
          `${API_BASE_URL}/generate-report`,
          {
            method: "POST",
            body: formData,
            credentials: "include",
          }
        );

      const contentType =
        response.headers.get(
          "content-type"
        ) || "";

      // --------------------------------------------------------
      // HANDLE BACKEND ERROR
      // --------------------------------------------------------

      if (!response.ok) {
        let errorMessage =
          `Report generation failed (${response.status}).`;

        if (
          contentType.includes(
            "application/json"
          )
        ) {
          try {
            const errorData =
              await response.json();

            if (errorData?.detail) {
              errorMessage =
                errorData.detail;
            }
          } catch {
            // Ignore JSON parsing error
          }
        } else {
          try {
            const text =
              await response.text();

            if (text) {
              errorMessage =
                text;
            }
          } catch {
            // Ignore response parsing error
          }
        }

        throw new Error(
          errorMessage
        );
      }

      // --------------------------------------------------------
      // VERIFY PDF RESPONSE
      // --------------------------------------------------------

      if (
        !contentType.includes(
          "application/pdf"
        )
      ) {
        throw new Error(
          `Backend did not return a PDF. Received: ${
            contentType ||
            "unknown response"
          }`
        );
      }

      // --------------------------------------------------------
      // GET PDF BLOB
      // --------------------------------------------------------

      const blob =
        await response.blob();

      if (
        !blob ||
        blob.size === 0
      ) {
        throw new Error(
          "The generated PDF is empty."
        );
      }

      // --------------------------------------------------------
      // DOWNLOAD PDF
      // --------------------------------------------------------

      const downloadUrl =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement(
          "a"
        );

      link.href =
        downloadUrl;

      link.download =
        `PARAKH-Inspection-Report-${Date.now()}.pdf`;

      document.body.appendChild(
        link
      );

      link.click();

      link.remove();

      // Delay revoke slightly so browser
      // has time to start download.
      setTimeout(() => {
        window.URL.revokeObjectURL(
          downloadUrl
        );
      }, 1000);

    } catch (err) {
      console.error(
        "PARAKH REPORT ERROR:",
        err
      );

      setError(
        err?.message ||
          "Unable to generate inspection report."
      );

    } finally {
      setGeneratingReport(false);
    }
  };

  // ============================================================
  // SAVE INSPECTOR FINAL DECISION
  // ============================================================

  const saveInspectorDecision =
    async (decision) => {
      const inspectionId =
        result?.inspection_id ||
        result?.id;

      if (!inspectionId) {
        setError(
          "Inspection ID is missing. Please run the analysis again."
        );
        return;
      }

      // Non-compliant requires remarks
      if (
        decision === "NON_COMPLIANT" &&
        !inspectorRemarks.trim()
      ) {
        setError(
          "Please enter Inspector remarks before marking the product non-compliant."
        );
        return;
      }

      const confirmed =
        window.confirm(
          decision === "COMPLIANT"
            ? "Confirm: Mark this inspection as COMPLIANT?"
            : "Confirm: Mark this inspection as NON-COMPLIANT?"
        );

      if (!confirmed) {
        return;
      }

      try {
        setSavingDecision(true);
        setDecisionSaved(false);
        setError("");

        const response =
          await fetch(
            `${API_BASE_URL}/history/${inspectionId}/decision`,
            {
              method: "PATCH",
              headers: {
                "Content-Type":
                  "application/json",
              },
              credentials: "include",
              body: JSON.stringify({
                decision,
                inspector_name:
                  "PARAKH Inspector",
                remarks:
                  inspectorRemarks.trim(),
              }),
            }
          );

        let data = null;

        try {
          data =
            await response.json();
        } catch {
          data = null;
        }

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              `Unable to save Inspector decision (${response.status}).`
          );
        }

        const updatedInspection =
          data?.inspection ||
          data;

        setResult(
          (previous) => ({
            ...(previous || {}),
            ...(updatedInspection || {}),

            inspector_decision:
              updatedInspection?.inspector_decision ||
              decision,

            inspector_name:
              updatedInspection?.inspector_name ||
              "PARAKH Inspector",

            inspector_remarks:
              updatedInspection?.inspector_remarks ??
              inspectorRemarks.trim(),

            decision_timestamp:
              updatedInspection?.decision_timestamp ||
              new Date().toISOString(),
          })
        );

        setDecisionSaved(true);

      } catch (err) {
        console.error(
          "PARAKH INSPECTOR DECISION ERROR:",
          err
        );

        setError(
          err?.message ||
            "Unable to save Inspector decision."
        );

      } finally {
        setSavingDecision(false);
      }
    };

  // ============================================================
  // REMOVE IMAGE
  // ============================================================

  const removeImage = () => {
    if (image) {
      URL.revokeObjectURL(
        image
      );
    }

    setImage(null);
    setFile(null);
    setResult(null);
    setInspectorRemarks("");
    setDecisionSaved(false);
    setError("");
    setAnalysisStage(0);
  };

  // ============================================================
  // STATUS HELPERS
  // ============================================================

  const getStatusClass =
    (status) => {
      const normalized =
        String(status || "")
          .toUpperCase()
          .replace(
            /-/g,
            "_"
          );

      switch (normalized) {
        case "PASS":
        case "COMPLIANT":
          return "inspection-status pass";

        case "FAIL":
        case "NON_COMPLIANT":
          return "inspection-status fail";

        case "NEEDS_REVIEW":
        case "REVIEW":
          return "inspection-status review";

        case "NOT_CHECKED":
          return "inspection-status pending";

        default:
          return "inspection-status pending";
      }
    };

  const getStatusIcon =
    (status) => {
      const normalized =
        String(status || "")
          .toUpperCase()
          .replace(
            /-/g,
            "_"
          );

      switch (normalized) {
        case "PASS":
        case "COMPLIANT":
          return "✓";

        case "FAIL":
        case "NON_COMPLIANT":
          return "✕";

        case "NEEDS_REVIEW":
        case "REVIEW":
          return "⚠";

        default:
          return "•";
      }
    };

  // ============================================================
  // SAFE VALUE
  // ============================================================

  const displayValue = (
    value,
    fallback = "Not detected"
  ) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return fallback;
    }

    return value;
  };

  // ============================================================
  // SUMMARY
  // ============================================================

  const summary =
    result?.summary || {};

  const compliance =
    result?.compliance || {};

  const complianceScore =
    summary.compliance_score ??
    summary.score ??
    compliance.score ??
    null;

  const overallStatus =
    summary.overall_status ??
    summary.status ??
    compliance.status ??
    "NEEDS_REVIEW";

  const passed =
    summary.passed ??
    summary.pass_count ??
    compliance.passed ??
    0;

  const failed =
    summary.failed ??
    summary.fail_count ??
    compliance.failed ??
    0;

  const needsReview =
    summary.needs_review ??
    summary.needsReview ??
    compliance.needs_review ??
    0;

  const notChecked =
    summary.not_checked ??
    summary.notChecked ??
    compliance.not_checked ??
    0;

  const inspectorDecision =
    result?.inspector_decision ||
    result?.final_decision ||
    result?.decision ||
    null;

  const inspectorName =
    result?.inspector_name ||
    "PARAKH Inspector";

  const savedRemarks =
    result?.inspector_remarks ||
    result?.remarks ||
    "";

  const finalDecisionStatus =
    inspectorDecision ||
    overallStatus;

  const checks =
    Array.isArray(
      result?.checks
    )
      ? result.checks
      : [];

  // ============================================================
  // ANALYSIS PROGRESS
  // ============================================================

  const progressPercent =
    Math.min(
      analysisStage * 25,
      100
    );

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <>
      {showCamera && !isMobileDevice && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={closeCamera}
        />
      )}

      <div className="inspection-page">

      {/* ======================================================
          PAGE HEADER
      ======================================================= */}

      <div className="page-header">

        <div>
          <h1>
            New Inspection
          </h1>

          <p>
            Upload a packaged product
            image for compliance analysis.
          </p>
        </div>

      </div>


      {/* ======================================================
          INSPECTION WORKSPACE
      ======================================================= */}

      <div className="inspection-grid">

        {/* ====================================================
            PRODUCT IMAGE
        ===================================================== */}

        <div className="upload-card">

          <div className="inspection-card-heading">
            <div>
              <span className="inspection-kicker">VISUAL INSPECTION</span>
              <h2>Product Image</h2>
            </div>
            <div className="inspection-orb" aria-hidden="true">
              <span />
            </div>
          </div>

          {!image ? (

            <>
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleCameraImage}
                hidden
              />

              <button
                type="button"
                className="camera-scan-button"
                onClick={openCamera}
                disabled={analyzing || generatingReport}
              >
                <span className="camera-scan-icon" aria-hidden="true">📷</span>
                <span>
                  <strong>Scan Product</strong>
                  <small>
                    {isMobileDevice
                      ? "Use your phone camera"
                      : "Use your laptop camera"}
                  </small>
                </span>
              </button>

              <div className="camera-or-divider" aria-hidden="true"><span>OR</span></div>

              <label
                className="upload-area"
            >

              <div className="upload-3d-visual" aria-hidden="true">
                <div className="upload-3d-ring ring-a" />
                <div className="upload-3d-ring ring-b" />
                <div className="upload-3d-cube">
                  <span className="cube-top" />
                  <span className="cube-front" />
                  <span className="cube-side" />
                  <span className="cube-scan" />
                </div>
                <div className="upload-scan-beam" />
              </div>

              <div className="upload-icon">
                +
              </div>

              <h3>
                Upload product image
              </h3>

              <p>
                PNG, JPG, JPEG or WebP
              </p>

              <span className="upload-button">
                Choose Image
              </span>

              <input
                type="file"
                accept="
                  image/png,
                  image/jpeg,
                  image/jpg,
                  image/webp
                "
                onChange={
                  handleImageChange
                }
                disabled={
                  analyzing ||
                  generatingReport
                }
                hidden
              />

              </label>
            </>

          ) : (

            <div className="image-preview">

              <div className="preview-frame">
                <div className="preview-corner corner-tl" />
                <div className="preview-corner corner-tr" />
                <div className="preview-corner corner-bl" />
                <div className="preview-corner corner-br" />
                <div className="preview-scan-line" />
                <img
                  src={image}
                  alt="Product preview"
                />
              </div>

              <button
                type="button"
                className="secondary-button"
                onClick={
                  removeImage
                }
                disabled={
                  analyzing ||
                  generatingReport
                }
              >
                Remove Image
              </button>

            </div>

          )}

        </div>


        {/* ====================================================
            INSPECTION DETAILS
        ===================================================== */}

        <div className="inspection-info">

          <div className="info-card">

            <h2>
              Inspection Details
            </h2>

            <div className="info-row">

              <span>
                Status
              </span>

              <strong>
                {analyzing
                  ? "Analyzing..."
                  : result
                  ? "Analysis Complete"
                  : "Ready"}
              </strong>

            </div>


            <div className="info-row">

              <span>
                Image
              </span>

              <strong>
                {file
                  ? "Uploaded"
                  : "Not uploaded"}
              </strong>

            </div>


            <div className="info-row">

              <span>
                Analysis
              </span>

              <strong>
                {analyzing
                  ? "Processing..."
                  : result
                  ? "Completed"
                  : "Not started"}
              </strong>

            </div>


{file && (
  <>
    <div className="info-row">
      <span>
        File
      </span>

      <strong
        title={file.name}
        style={{
          maxWidth: "180px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {file.name}
      </strong>
    </div>

    <div className="info-row">
      <span>
        Size
      </span>

      <strong>
        {(file.size / 1024 / 1024).toFixed(2)} MB
      </strong>
    </div>
  </>
)}
          </div>


          {/* ==================================================
              ANALYZE BUTTON
          =================================================== */}

          <button
            type="button"
            className="analyze-button"
            disabled={
              !file ||
              processingImage ||
              analyzing ||
              generatingReport
            }
            onClick={
              analyzeProduct
            }
          >
            {analyzing
              ? "Analyzing..."
              : "Analyze Product"}
          </button>


          {/* ==================================================
              ANALYSIS PROGRESS
          =================================================== */}

          {analyzing && (

            <div className="analysis-progress">

              <div className="analysis-progress-header">

                <div>

                  <h3>
                    PARAKH AI Analysis
                  </h3>

                  <p>
                    Inspecting package
                    declarations and
                    compliance requirements.
                  </p>

                </div>

                <div className="analysis-spinner">
                  ◌
                </div>

              </div>


              <div className="analysis-steps">

                {/* STEP 1 */}

                <div
                  className={
                    analysisStage >= 1
                      ? "analysis-step active"
                      : "analysis-step"
                  }
                >

                  <span>
                    {analysisStage > 1
                      ? "✓"
                      : "1"}
                  </span>

                  <div>

                    <strong>
                      Reading package image
                    </strong>

                    <small>
                      Processing uploaded image
                    </small>

                  </div>

                </div>


                {/* STEP 2 */}

                <div
                  className={
                    analysisStage >= 2
                      ? "analysis-step active"
                      : "analysis-step"
                  }
                >

                  <span>
                    {analysisStage > 2
                      ? "✓"
                      : "2"}
                  </span>

                  <div>

                    <strong>
                      Extracting declarations
                    </strong>

                    <small>
                      Detecting product information
                    </small>

                  </div>

                </div>


                {/* STEP 3 */}

                <div
                  className={
                    analysisStage >= 3
                      ? "analysis-step active"
                      : "analysis-step"
                  }
                >

                  <span>
                    {analysisStage > 3
                      ? "✓"
                      : "3"}
                  </span>

                  <div>

                    <strong>
                      Checking compliance
                    </strong>

                    <small>
                      Applying Legal Metrology rules
                    </small>

                  </div>

                </div>


                {/* STEP 4 */}

                <div
                  className={
                    analysisStage >= 4
                      ? "analysis-step active"
                      : "analysis-step"
                  }
                >

                  <span>
                    {analysisStage >= 4
                      ? "✓"
                      : "4"}
                  </span>

                  <div>

                    <strong>
                      Finalizing inspection
                    </strong>

                    <small>
                      Preparing compliance result
                    </small>

                  </div>

                </div>

              </div>


              <div className="analysis-progress-bar">

                <div
                  className="analysis-progress-fill"
                  style={{
                    width:
                      `${progressPercent}%`,
                  }}
                />

              </div>


              <div className="analysis-progress-percent">
                {progressPercent}%
              </div>

            </div>

          )}


          {/* ==================================================
              REPORT BUTTON
          =================================================== */}

          {result && (

            <button
              type="button"
              className="report-button"
              disabled={
                generatingReport ||
                analyzing
              }
              onClick={
                generateReport
              }
            >

              {generatingReport
                ? "Generating Report..."
                : "📄 Generate Inspection Report"}

            </button>

          )}


          {/* ==================================================
              ERROR
          =================================================== */}

          {error && (

            <div className="error-message">
              {error}
            </div>

          )}

        </div>

      </div>


      {/* ======================================================
          ANALYSIS RESULT
      ======================================================= */}

      {result && (

        <div className="analysis-result">

          {/* ==================================================
              RESULT HEADER
          =================================================== */}

          <div className="result-header">

            <div>

              <h2>
                Inspection Result
              </h2>

              <p>
                Product information extracted
                and checked by PARAKH.
              </p>

            </div>


            <div
              className={
                getStatusClass(
                  overallStatus
                )
              }
            >

              <span>
                {getStatusIcon(
                  overallStatus
                )}
              </span>

              {String(
                overallStatus
              ).replace(
                /_/g,
                " "
              )}

            </div>

          </div>


          {/* ==================================================
              SCORE SECTION
          =================================================== */}

          <div className="inspection-score-section">

            <div className="main-score">

              <span>
                Compliance Score
              </span>

              <strong>
                {complianceScore !==
                  null &&
                complianceScore !==
                  undefined
                  ? `${complianceScore}%`
                  : "—"}
              </strong>

              <small>
                {complianceScore !== null &&
                complianceScore !== undefined
                  ? "Based on resolved mandatory checks"
                  : String(overallStatus).toUpperCase() === "NEEDS_REVIEW"
                  ? "Score withheld until required evidence is verified"
                  : "No resolved mandatory checks"}
              </small>

            </div>


            <div className="score-stat">

              <span>
                Passed
              </span>

              <strong>
                {passed}
              </strong>

            </div>


            <div className="score-stat">

              <span>
                Failed
              </span>

              <strong>
                {failed}
              </strong>

            </div>


            <div className="score-stat">

              <span>
                Needs Review
              </span>

              <strong>
                {needsReview}
              </strong>

            </div>


            <div className="score-stat">

              <span>
                Not Checked
              </span>

              <strong>
                {notChecked}
              </strong>

            </div>

          </div>


          {/* ==================================================
              PRODUCT INFORMATION
          =================================================== */}

          <section className="result-section">

            <div className="section-heading">

              <div>

                <h3>
                  Product Information
                </h3>

                <span>
                  Detected by PARAKH
                </span>

              </div>

            </div>


            <div className="product-details">

              <div>

                <span>
                  Product Name
                </span>

                <strong>
                  {displayValue(
                    result.product?.name
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Brand
                </span>

                <strong>
                  {displayValue(
                    result.product?.brand
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Commodity
                </span>

                <strong>
                  {displayValue(
                    result.product?.commodity
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Net Quantity
                </span>

                <strong>
                  {displayValue(
                    result.product
                      ?.net_quantity
                  )}
                </strong>

              </div>


              <div>

                <span>
                  MRP
                </span>

                <strong>
                  {displayValue(
                    result.product?.mrp
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Manufacturer
                </span>

                <strong>
                  {displayValue(
                    result.product
                      ?.manufacturer
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Packaging Date
                </span>

                <strong>
                  {displayValue(
                    result.product
                      ?.packaging_date
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Best Before
                </span>

                <strong>
                  {displayValue(
                    result.product
                      ?.best_before
                  )}
                </strong>

              </div>


              <div>

                <span>
                  FSSAI / Food License
                </span>

                <strong>
                  {displayValue(
                    result.product
                      ?.food_license ||
                    result.product
                      ?.fssai_license
                  )}
                </strong>

              </div>

            </div>

          </section>


          {/* ==================================================
              LEGAL COMPLIANCE
          =================================================== */}

          <section className="result-section">

            <div className="section-heading">

              <div>

                <h3>
                  Legal Compliance Checks
                </h3>

                <span>
                  Rule-based verification of
                  package declarations.
                </span>

              </div>

            </div>


            <div className="compliance-list">

              {checks.length > 0 ? (

                checks.map(
                  (
                    check,
                    index
                  ) => {

                    const confidence =
                      Number(
                        check?.confidence ??
                          0
                      );

                    const confidencePercent =
                      confidence <= 1
                        ? Math.round(
                            confidence *
                              100
                          )
                        : Math.round(
                            confidence
                          );

                    return (

                      <div
                        className="compliance-item"
                        key={
                          check?.rule_id ||
                          `${check?.field}-${index}`
                        }
                      >

                        {/* ICON */}

                        <div className="compliance-icon">

                          {getStatusIcon(
                            check?.status
                          )}

                        </div>


                        {/* CONTENT */}

                        <div className="compliance-content">

                          <div className="compliance-title">

                            <strong>
                              {displayValue(
                                check?.field,
                                "Compliance Requirement"
                              )}
                            </strong>

                            <span>
                              Rule{" "}
                              {displayValue(
                                check?.rule_number,
                                "-"
                              )}
                            </span>

                          </div>


                          <p>
                            {displayValue(
                              check?.description,
                              "No description available."
                            )}
                          </p>


                          {/* DETECTED VALUE */}

                          {check?.value !==
                            undefined &&
                          check?.value !==
                            null &&
                          check?.value !==
                            "" && (

                            <div className="compliance-reason">

                              <strong>
                                Detected Value:
                              </strong>{" "}

                              {String(
                                check.value
                              )}

                            </div>

                          )}


                          {/* REASON */}

                          {check?.reason && (

                            <div className="compliance-reason">

                              <strong>
                                Finding:
                              </strong>{" "}

                              {check.reason}

                            </div>

                          )}


                          {/* CONFIDENCE */}

                          <div className="confidence-row">

                            <span>
                              Confidence
                            </span>

                            <strong>
                              {confidencePercent}%
                            </strong>

                          </div>


                          {/* EVIDENCE */}

                          {Array.isArray(
                            check?.evidence
                          ) &&
                          check.evidence
                            .length > 0 && (

                            <div className="evidence-box">

                              <strong>
                                Evidence
                              </strong>

                              {check.evidence.map(
                                (
                                  evidence,
                                  evidenceIndex
                                ) => (

                                  <div
                                    key={
                                      evidenceIndex
                                    }
                                  >
                                    {evidence}
                                  </div>

                                )
                              )}

                            </div>

                          )}


                          {/* CANDIDATES */}

                          {Array.isArray(
                            check?.candidates
                          ) &&
                          check.candidates
                            .length > 0 && (

                            <div className="review-box">

                              <strong>
                                ⚠ Conflicting Values
                              </strong>

                              <p>
                                PARAKH found
                                multiple possible
                                values. Manual
                                verification is
                                required.
                              </p>

                              {check.candidates.map(
                                (
                                  candidate,
                                  candidateIndex
                                ) => (

                                  <div
                                    key={
                                      candidateIndex
                                    }
                                  >
                                    •{" "}
                                    {candidate}
                                  </div>

                                )
                              )}

                            </div>

                          )}

                        </div>


                        {/* STATUS */}

                        <div
                          className={
                            getStatusClass(
                              check?.status
                            )
                          }
                        >

                          {getStatusIcon(
                            check?.status
                          )}{" "}

                          {String(
                            check?.status ||
                              "NOT_CHECKED"
                          ).replace(
                            /_/g,
                            " "
                          )}

                        </div>

                      </div>

                    );

                  }
                )

              ) : (

                <div className="review-box">

                  No compliance checks
                  were returned by the
                  backend.

                </div>

              )}

            </div>

          </section>


          {/* ==================================================
              FINAL INSPECTION SUMMARY
          =================================================== */}

          <section className="result-section">

            <div className="section-heading">

              <div>

                <h3>
                  Inspection Summary
                </h3>

                <span>
                  Final assessment generated
                  by PARAKH.
                </span>

              </div>

            </div>


            <div className="final-summary">

              <div>

                <span>
                  Total Checks
                </span>

                <strong>
                  {summary.total_checks ??
                    checks.length ??
                    0}
                </strong>

              </div>


              <div>

                <span>
                  Passed
                </span>

                <strong>
                  {passed}
                </strong>

              </div>


              <div>

                <span>
                  Failed
                </span>

                <strong>
                  {failed}
                </strong>

              </div>


              <div>

                <span>
                  Needs Review
                </span>

                <strong>
                  {needsReview}
                </strong>

              </div>


              <div>

                <span>
                  Not Checked
                </span>

                <strong>
                  {notChecked}
                </strong>

              </div>

            </div>


            <div className="inspection-note">

              <strong>
                Inspection Decision
              </strong>

              <p>

                {String(
                  overallStatus
                ).toUpperCase() ===
                "COMPLIANT"

                  ? "No failed or ambiguous mandatory checks were detected."

                  : String(
                      overallStatus
                    ).toUpperCase() ===
                    "NON_COMPLIANT"

                  ? "One or more mandatory compliance requirements failed validation."

                  : "One or more declarations require manual verification before a final compliance decision can be made."
                }

              </p>

            </div>

          </section>


          {/* ==================================================
              INSPECTOR FINAL DECISION
          =================================================== */}

          <section className="result-section inspector-decision-section">

            <div className="section-heading inspector-decision-heading">

              <div>

                <span className="decision-kicker">
                  FINAL VERIFICATION
                </span>

                <h3>
                  Inspector Decision
                </h3>

                <span>
                  Review the AI findings and evidence before recording the final inspection decision.
                </span>

              </div>


              <div
                className={getStatusClass(
                  finalDecisionStatus
                )}
              >

                <span>
                  {getStatusIcon(
                    finalDecisionStatus
                  )}
                </span>

                {String(
                  finalDecisionStatus
                ).replace(
                  /_/g,
                  " "
                )}

              </div>

            </div>


            {inspectorDecision ? (

              <div className="decision-success">

                <div className="decision-success-icon">
                  ✓
                </div>

                <div>

                  <strong>
                    Final decision recorded:{" "}
                    {String(
                      inspectorDecision
                    ).replace(
                      /_/g,
                      " "
                    )}
                  </strong>

                  <p>
                    {inspectorName}

                    {savedRemarks
                      ? ` — ${savedRemarks}`
                      : " — No additional remarks provided."}
                  </p>

                </div>

              </div>

            ) : (

              <>

                <div className="inspector-remarks">

                  <label
                    htmlFor="inspector-remarks"
                  >
                    Inspector Remarks
                  </label>

                  <textarea
                    id="inspector-remarks"
                    value={
                      inspectorRemarks
                    }
                    onChange={(
                      event
                    ) =>
                      setInspectorRemarks(
                        event.target.value
                      )
                    }
                    placeholder="Enter verification observations, evidence notes or the reason for the final decision..."
                    rows={4}
                    disabled={
                      savingDecision
                    }
                  />

                  <small>
                    Remarks are required when marking an inspection non-compliant.
                  </small>

                </div>


                <div className="decision-buttons">

                  <button
                    type="button"
                    className="decision-button decision-compliant"
                    disabled={
                      savingDecision ||
                      generatingReport ||
                      analyzing
                    }
                    onClick={() =>
                      saveInspectorDecision(
                        "COMPLIANT"
                      )
                    }
                  >

                    <span className="decision-button-icon">
                      ✓
                    </span>

                    <span>

                      <strong>
                        Mark Compliant
                      </strong>

                      <small>
                        Confirm that the reviewed package meets the requirements.
                      </small>

                    </span>

                  </button>


                  <button
                    type="button"
                    className="decision-button decision-non-compliant"
                    disabled={
                      savingDecision ||
                      generatingReport ||
                      analyzing
                    }
                    onClick={() =>
                      saveInspectorDecision(
                        "NON_COMPLIANT"
                      )
                    }
                  >

                    <span className="decision-button-icon">
                      !
                    </span>

                    <span>

                      <strong>
                        Mark Non-Compliant
                      </strong>

                      <small>
                        Record a violation after reviewing the available evidence.
                      </small>

                    </span>

                  </button>

                </div>


                {savingDecision && (

                  <div className="decision-saving">
                    Saving Inspector decision...
                  </div>

                )}


                {decisionSaved && (

                  <div className="decision-success">

                    <div className="decision-success-icon">
                      ✓
                    </div>

                    <div>

                      <strong>
                        Decision saved successfully
                      </strong>

                      <p>
                        The final Inspector decision has been saved to inspection history.
                      </p>

                    </div>

                  </div>

                )}

              </>

            )}

          </section>


          {/* ==================================================
              OCR EVIDENCE
          =================================================== */}

          <section className="result-section">

            <details className="ocr-section">

              <summary>
                View OCR Text / Evidence
              </summary>

              <pre>
                {result?.ocr_text ||
                  "No OCR text available."}
              </pre>

            </details>

          </section>


          {/* ==================================================
              REPORT ACTION
          =================================================== */}

          <div className="report-action-section">

            <button
              type="button"
              className="report-button"
              disabled={
                generatingReport ||
                analyzing
              }
              onClick={
                generateReport
              }
            >

              {generatingReport
                ? "Generating PDF Report..."
                : "📄 Generate & Download Inspection Report"}

            </button>


            <p>
              The report contains product
              information, compliance findings,
              evidence, confidence scores and
              OCR evidence.
            </p>

          </div>

        </div>

      )}

      </div>
    </>
  );
}

export default Inspection;