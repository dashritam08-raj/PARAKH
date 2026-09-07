import { useState } from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import "./Auth.css";

import { API_BASE_URL } from "../config/api";

function Register() {
  const navigate = useNavigate();

  const [name, setName] =
    useState("");
  const [email, setEmail] =
    useState("");
  const [password, setPassword] =
    useState("");
  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");
  const [error, setError] =
    useState("");

  // ============================================================
  // REGISTER
  // ============================================================
  const handleRegister = async (event) => {
    event.preventDefault();
    setError("");

    const cleanName =
      name.trim();

    const cleanEmail =
      email.trim().toLowerCase();

    // ========================================================
    // PASSWORD LENGTH
    // ========================================================
    if (password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    // ========================================================
    // CONFIRM PASSWORD
    // ========================================================
    if (
      password !==
      confirmPassword
    ) {
      setError(
        "Passwords do not match."
      );
      return;
    }

    // ========================================================
    // NAME VALIDATION
    // ========================================================
    if (!cleanName) {
      setError(
        "Please enter your full name."
      );
      return;
    }

    try {
      // ========================================================
      // SEND REGISTRATION REQUEST TO SECURE BACKEND
      // ========================================================
      const formData = new FormData();

      formData.append(
        "name",
        cleanName
      );

      formData.append(
        "email",
        cleanEmail
      );

      formData.append(
        "password",
        password
      );

      const response = await fetch(
        `${API_BASE_URL}/auth/register`,
        {
          method: "POST",
          body: formData,
          credentials: "include",
        }
      );

      let data = {};

      try {
        data = await response.json();
      } catch {
        data = {};
      }

      // ========================================================
      // REGISTRATION FAILED
      // ========================================================
      if (!response.ok) {
        setError(
          data.detail ||
            data.message ||
            "Registration failed. Please try again."
        );

        return;
      }

      // ========================================================
      // SAVE SAFE USER INFORMATION ONLY
      // ========================================================
      // Password and session token are NOT stored in localStorage.
      const registeredUser =
        data.user || {};

      localStorage.setItem(
        "parakh_user",
        JSON.stringify({
          name:
            registeredUser.name ||
            cleanName,
          email:
            registeredUser.email ||
            cleanEmail,
          role:
            registeredUser.role ||
            "INSPECTOR",
        })
      );

      // ========================================================
      // AUTHENTICATION FLAG
      // ========================================================
      // App.jsx currently uses this flag for client-side routing.
      // The actual authenticated session is maintained by the
      // backend through the HttpOnly session cookie.
      localStorage.setItem(
        "parakh_authenticated",
        "true"
      );

      // ========================================================
      // GO TO DASHBOARD
      // ========================================================
      navigate(
        "/",
        {
          replace: true,
        }
      );
    } catch (requestError) {
      console.error(
        "Registration request failed:",
        requestError
      );

      setError(
        "Cannot connect to the PARAKH server. Please make sure the backend is running."
      );
    }
  };

  // ============================================================
  // UI
  // ============================================================
  return (
    <div className="auth-page">
      <div className="auth-layout">

        {/* =====================================================
            LEFT — PARAKH VISUAL
        ====================================================== */}
        <div className="auth-visual">
          {/* Orbit rings */}
          <div
            className="auth-orbit orbit-one"
          />
          <div
            className="auth-orbit orbit-two"
          />

          {/* Logo */}
          <div className="auth-visual-logo">
            <img
              src="/parakh-logo.jpeg"
              alt="PARAKH"
            />
          </div>

          {/* Brand */}
          <div className="auth-visual-title">
            PARAKH
          </div>

          <div className="auth-visual-subtitle">
            AI-POWERED INSPECTION
          </div>

          {/* Engine status */}
          <div className="auth-engine-status">
            <span
              className="auth-status-dot"
            />
            <span>
              INSPECTION ENGINE ONLINE
            </span>
          </div>

          {/* Process */}
          <div className="auth-process">
            <span>
              SCAN
            </span>
            <b>
              →
            </b>
            <span>
              ANALYZE
            </span>
            <b>
              →
            </b>
            <span>
              VERIFY
            </span>
          </div>
        </div>

        {/* =====================================================
            RIGHT — REGISTER CARD
        ====================================================== */}
        <div className="auth-card">

          {/* =================================================
              BRAND
          ================================================== */}
          <div className="auth-brand">
            <div className="auth-logo">
              <img
                src="/parakh-logo.jpeg"
                alt="PARAKH Logo"
              />
            </div>

            <div className="auth-brand-text">
              <h1>
                PARAKH
              </h1>
              <span>
                Legal Metrology
              </span>
            </div>
          </div>

          {/* =================================================
              HEADER
          ================================================== */}
          <div className="auth-header">
            <h2>
              Create Inspector Account
            </h2>
            <p>
              Register to access the
              PARAKH inspection platform.
            </p>
          </div>

          {/* =================================================
              ERROR
          ================================================= */}
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          {/* =================================================
              REGISTER FORM
          ================================================= */}
          <form
            onSubmit={handleRegister}
          >

            {/* FULL NAME */}
            <div className="form-group">
              <label htmlFor="name">
                Full name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value
                  )
                }
                placeholder="Enter your name"
                autoComplete="name"
                required
              />
            </div>

            {/* EMAIL */}
            <div className="form-group">
              <label htmlFor="register-email">
                Email address
              </label>
              <input
                id="register-email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(
                    event.target.value
                  )
                }
                placeholder="inspector@example.com"
                autoComplete="email"
                required
              />
            </div>

            {/* PASSWORD */}
            <div className="form-group">
              <label htmlFor="register-password">
                Password
              </label>
              <input
                id="register-password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                placeholder="Minimum 6 characters"
                autoComplete="new-password"
                required
              />
            </div>

            {/* CONFIRM PASSWORD */}
            <div className="form-group">
              <label htmlFor="confirm-password">
                Confirm password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value
                  )
                }
                placeholder="Confirm your password"
                autoComplete="new-password"
                required
              />
            </div>

            {/* SUBMIT */}
            <button
              type="submit"
              className="auth-submit"
            >
              Create account
            </button>
          </form>

          {/* =================================================
              LOGIN
          ================================================== */}
          <div className="auth-footer">
            <span>
              Already have an account?
            </span>
            <Link to="/login">
              Sign in
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Register;
