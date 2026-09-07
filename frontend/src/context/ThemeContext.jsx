import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

const ThemeContext = createContext(null);

function getSystemTheme() {
  return window.matchMedia(
    "(prefers-color-scheme: dark)"
  ).matches
    ? "dark"
    : "light";
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return (
      localStorage.getItem("parakh_theme") ||
      "system"
    );
  });

  useEffect(() => {
    localStorage.setItem(
      "parakh_theme",
      theme
    );
  }, [theme]);

  useEffect(() => {
    const mediaQuery = window.matchMedia(
      "(prefers-color-scheme: dark)"
    );

    const applyTheme = () => {
      const actualTheme =
        theme === "system"
          ? getSystemTheme()
          : theme;

      document.documentElement.setAttribute(
        "data-theme",
        actualTheme
      );
    };

    applyTheme();

    if (theme === "system") {
      mediaQuery.addEventListener(
        "change",
        applyTheme
      );
    }

    return () => {
      mediaQuery.removeEventListener(
        "change",
        applyTheme
      );
    };
  }, [theme]);

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context =
    useContext(ThemeContext);

  if (!context) {
    throw new Error(
      "useTheme must be used inside ThemeProvider"
    );
  }

  return context;
}