import { useEffect, useState } from "react";

import SplashScreen from "./components/SplashScreen";

import "./App.css";

import { ThemeProvider } from "./context/ThemeContext";

import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import Sidebar from "./components/Sidebar";

import Dashboard from "./pages/Dashboard";
import Inspection from "./pages/Inspection";
import InspectionHistory from "./pages/InspectionHistory";
import InspectionDetails from "./pages/InspectionDetails";

import Login from "./pages/Login";
import Register from "./pages/Register";


// ============================================================
// AUTH CHECK
// ============================================================

function isAuthenticated() {
  return (
    localStorage.getItem("parakh_authenticated") === "true"
  );
}


// ============================================================
// PROTECTED ROUTE
// ============================================================

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  return children;
}


// ============================================================
// PUBLIC ROUTE
// ============================================================

function PublicRoute({ children }) {
  if (isAuthenticated()) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  return children;
}


// ============================================================
// APP
// ============================================================

function App() {

  // ----------------------------------------------------------
  // SPLASH SCREEN
  // ----------------------------------------------------------

  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {

    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 1900);

    return () => clearTimeout(timer);

  }, []);


  // ----------------------------------------------------------
  // APP
  // ----------------------------------------------------------

  return (
    <>
      {/* =====================================================
          PARAKH SPLASH SCREEN
      ====================================================== */}

      {showSplash && <SplashScreen />}


      {/* =====================================================
          APPLICATION
      ====================================================== */}

      <ThemeProvider>

        <BrowserRouter>

          <Routes>

            {/* =================================================
                LOGIN
            ================================================== */}

            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />


            {/* =================================================
                REGISTER
            ================================================== */}

            <Route
              path="/register"
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              }
            />


            {/* =================================================
                PROTECTED APPLICATION
            ================================================== */}

            <Route
              path="/*"
              element={
                <ProtectedRoute>

                  <div className="app">

                    {/* -----------------------------------------
                        SIDEBAR
                    ------------------------------------------ */}

                    <Sidebar />


                    {/* -----------------------------------------
                        MAIN CONTENT
                    ------------------------------------------ */}

                    <main className="main-content">

                      <Routes>

                        {/* =====================================
                            DASHBOARD
                        ====================================== */}

                        <Route
                          path="/"
                          element={
                            <Dashboard />
                          }
                        />


                        {/* =====================================
                            NEW INSPECTION
                        ====================================== */}

                        <Route
                          path="/inspection"
                          element={
                            <Inspection />
                          }
                        />


                        {/* =====================================
                            INSPECTION HISTORY
                        ====================================== */}

                        <Route
                          path="/history"
                          element={
                            <InspectionHistory />
                          }
                        />


                        {/* =====================================
                            INSPECTION DETAILS
                        ====================================== */}

                        <Route
                          path="/inspection-details"
                          element={
                            <InspectionDetails />
                          }
                        />


                        {/* =====================================
                            DASHBOARD ALIAS
                        ====================================== */}

                        <Route
                          path="/dashboard"
                          element={
                            <Navigate
                              to="/"
                              replace
                            />
                          }
                        />


                        {/* =====================================
                            NEW INSPECTION ALIAS
                        ====================================== */}

                        <Route
                          path="/new-inspection"
                          element={
                            <Navigate
                              to="/inspection"
                              replace
                            />
                          }
                        />


                        {/* =====================================
                            SETTINGS
                        ====================================== */}

                        <Route
                          path="/settings"
                          element={
                            <Navigate
                              to="/"
                              replace
                            />
                          }
                        />


                        {/* =====================================
                            UNKNOWN ROUTE
                        ====================================== */}

                        <Route
                          path="*"
                          element={
                            <Navigate
                              to="/"
                              replace
                            />
                          }
                        />

                      </Routes>

                    </main>

                  </div>

                </ProtectedRoute>
              }
            />

          </Routes>

        </BrowserRouter>

      </ThemeProvider>

    </>
  );
}


export default App;