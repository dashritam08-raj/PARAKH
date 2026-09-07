import { useState } from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import "./Auth.css";

import { API_BASE_URL } from "../config/api";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] =
    useState("");
  const [password, setPassword] =
    useState("");
  const [error, setError] =
    useState("");

  // ============================================================
  // LOGIN
  // ============================================================
  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");

    const cleanEmail =
      email.trim().toLowerCase();

    if (!cleanEmail || !password) {
      setError(
        "Please enter your email and password."
      );
      return;
    }

    try {
      // ========================================================
      // SEND LOGIN REQUEST TO SECURE BACKEND
      // ========================================================
      const formData = new FormData();

      formData.append(
        "email",
        cleanEmail
      );

      formData.append(
        "password",
        password
      );

      const response = await fetch(
        `${API_BASE_URL}/auth/login`,
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
      // LOGIN FAILED
      // ========================================================
      if (!response.ok) {
        setError(
          data.detail ||
            data.message ||
            "Incorrect email or password."
        );

        return;
      }

      // ========================================================
      // SAVE SAFE USER INFORMATION ONLY
      // ========================================================
      // Password and session token are NOT stored in localStorage.
      if (data.user) {
        localStorage.setItem(
          "parakh_user",
          JSON.stringify({
            name:
              data.user.name || "",
            email:
              data.user.email ||
              cleanEmail,
            role:
              data.user.role ||
              "INSPECTOR",
          })
        );
      }

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
      // LOGIN SUCCESS
      // ========================================================
      navigate(
        "/",
        {
          replace: true,
        }
      );
    } catch (requestError) {
      console.error(
        "Login request failed:",
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
            RIGHT — LOGIN CARD
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
              Welcome back
            </h2>
            <p>
              Sign in to continue
              your inspection work.
            </p>
          </div>

          {/* =================================================
              ERROR
          ================================================== */}
          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          {/* =================================================
              LOGIN FORM
          ================================================== */}
          <form
            onSubmit={handleLogin}
          >

            {/* EMAIL */}
            <div className="form-group">
              <label htmlFor="email">
                Email address
              </label>
              <input
                id="email"
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
              <label htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />
            </div>

            {/* SUBMIT */}
            <button
              type="submit"
              className="auth-submit"
            >
              Sign in
            </button>
          </form>

          {/* =================================================
              REGISTER
          ================================================== */}
          <div className="auth-footer">
            <span>
              Don't have an account?
            </span>
            <Link to="/register">
              Create account
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Login;
