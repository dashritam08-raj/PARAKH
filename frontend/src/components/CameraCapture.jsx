import { useCallback, useEffect, useRef, useState } from "react";
import "./CameraCapture.css";

function CameraCapture({ onCapture, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const previewUrlRef = useRef(null);

  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [capturedFile, setCapturedFile] = useState(null);
  const [capturedPreview, setCapturedPreview] = useState(null);
  const [capturing, setCapturing] = useState(false);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraReady(false);
  }, []);

  const startCamera = useCallback(async () => {
    setCameraError("");
    setCameraReady(false);

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError(
        "Camera access is not supported by this browser. Please use Upload Image instead."
      );
      return;
    }

    try {
      stopCamera();

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "user" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraReady(true);
      }
    } catch (error) {
      console.error("PARAKH CAMERA ERROR:", error);

      let message =
        "Unable to access the camera. Please allow camera permission and try again.";

      if (error?.name === "NotAllowedError") {
        message =
          "Camera permission was denied. Allow camera access in your browser settings and try again.";
      } else if (error?.name === "NotFoundError") {
        message = "No camera was found on this device.";
      } else if (error?.name === "NotReadableError") {
        message =
          "The camera is currently being used by another application.";
      } else if (error?.name === "SecurityError") {
        message =
          "Camera access was blocked by the browser security policy. Use PARAKH over HTTPS on production.";
      }

      setCameraError(message);
    }
  }, [stopCamera]);

  useEffect(() => {
    startCamera();

    return () => {
      stopCamera();

      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
        previewUrlRef.current = null;
      }
    };
  }, [startCamera, stopCamera]);

  const capturePhoto = () => {
    if (!videoRef.current || !cameraReady || capturing) {
      return;
    }

    setCapturing(true);

    try {
      const video = videoRef.current;
      const canvas = document.createElement("canvas");

      const width = video.videoWidth || 1280;
      const height = video.videoHeight || 720;

      canvas.width = width;
      canvas.height = height;

      const context = canvas.getContext("2d");

      if (!context) {
        throw new Error("Unable to prepare the camera image.");
      }

      context.drawImage(video, 0, 0, width, height);

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            setCameraError(
              "Unable to capture the product image. Please try again."
            );
            setCapturing(false);
            return;
          }

          const file = new File(
            [blob],
            `PARAKH-Camera-${Date.now()}.jpg`,
            { type: "image/jpeg" }
          );

          if (previewUrlRef.current) {
            URL.revokeObjectURL(previewUrlRef.current);
          }

          const preview = URL.createObjectURL(blob);
          previewUrlRef.current = preview;

          setCapturedFile(file);
          setCapturedPreview(preview);

          stopCamera();
          setCapturing(false);
        },
        "image/jpeg",
        0.92
      );
    } catch (error) {
      console.error("PARAKH CAPTURE ERROR:", error);

      setCameraError(
        error?.message || "Unable to capture the product image."
      );

      setCapturing(false);
    }
  };

  const retakePhoto = () => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }

    setCapturedFile(null);
    setCapturedPreview(null);
    setCameraError("");
    startCamera();
  };

  const usePhoto = () => {
    if (capturedFile) {
      onCapture(capturedFile);
    }
  };

  const handleClose = () => {
    stopCamera();
    onClose();
  };

  return (
    <div
      className="camera-modal"
      role="dialog"
      aria-modal="true"
      aria-label="Scan product"
    >
      <div
        className="camera-modal-backdrop"
        onClick={handleClose}
      />

      <div className="camera-panel">
        <div className="camera-header">
          <div>
            <span className="camera-kicker">PARAKH VISION</span>
            <h2>Scan Product</h2>
            <p>Position the package inside the frame.</p>
          </div>

          <button
            type="button"
            className="camera-close-button"
            onClick={handleClose}
            aria-label="Close camera"
          >
            ×
          </button>
        </div>

        <div className="camera-view">
          {!capturedPreview ? (
            <>
              <video
                ref={videoRef}
                className="camera-video"
                autoPlay
                playsInline
                muted
              />

              <div className="camera-frame" aria-hidden="true">
                <span className="camera-corner tl" />
                <span className="camera-corner tr" />
                <span className="camera-corner bl" />
                <span className="camera-corner br" />
                <span className="camera-scan-line" />
              </div>

              <div className="camera-guide">
                Align the product label inside the frame
              </div>

              {cameraError && (
                <div className="camera-error">
                  {cameraError}
                </div>
              )}
            </>
          ) : (
            <div className="camera-captured-view">
              <img
                src={capturedPreview}
                alt="Captured product"
              />

              <div className="camera-captured-badge">
                ✓ Photo captured
              </div>
            </div>
          )}
        </div>

        <div className="camera-actions">
          {!capturedPreview ? (
            <>
              <button
                type="button"
                className="camera-secondary-button"
                onClick={handleClose}
              >
                Cancel
              </button>

              <button
                type="button"
                className="camera-capture-button"
                onClick={capturePhoto}
                disabled={!cameraReady || capturing}
              >
                <span
                  className="camera-shutter"
                  aria-hidden="true"
                />
                {capturing ? "Capturing..." : "Capture"}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="camera-secondary-button"
                onClick={retakePhoto}
              >
                ↻ Retake
              </button>

              <button
                type="button"
                className="camera-use-button"
                onClick={usePhoto}
              >
                ✓ Use Photo
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default CameraCapture;
