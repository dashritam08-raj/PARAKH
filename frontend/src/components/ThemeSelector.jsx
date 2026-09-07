import { useState } from "react";

import {
  useTheme,
} from "../context/ThemeContext";


function ThemeSelector() {

  const {
    theme,
    setTheme,
  } = useTheme();

  const [open, setOpen] =
    useState(false);


  const options = [
    {
      value: "light",
      label: "Light",
      icon: "☀",
    },
    {
      value: "dark",
      label: "Dark",
      icon: "☾",
    },
    {
      value: "system",
      label: "System Default",
      icon: "◐",
    },
  ];


  const selected =
    options.find(
      (option) =>
        option.value === theme
    ) || options[2];


  const handleSelect = (value) => {

    setTheme(value);

    setOpen(false);

  };


  return (

    <div className="theme-selector">

      <div className="theme-selector-label">
        Appearance
      </div>


      <button
        type="button"
        className="theme-selector-button"
        onClick={() =>
          setOpen(
            (previous) =>
              !previous
          )
        }
        aria-haspopup="listbox"
        aria-expanded={open}
      >

        <span className="theme-current-icon">
          {selected.icon}
        </span>


        <span className="theme-current-label">
          {selected.label}
        </span>


        <span className="theme-chevron">
          {open ? "⌃" : "⌄"}
        </span>

      </button>


      {open && (

        <div
          className="theme-menu"
          role="listbox"
        >

          {options.map(
            (option) => (

              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={
                  theme ===
                  option.value
                }
                className={`theme-option ${
                  theme ===
                  option.value
                    ? "selected"
                    : ""
                }`}
                onClick={() =>
                  handleSelect(
                    option.value
                  )
                }
              >

                <span className="theme-option-icon">
                  {option.icon}
                </span>


                <span className="theme-option-label">
                  {option.label}
                </span>


                {theme ===
                  option.value && (

                  <span className="theme-check">
                    ✓
                  </span>

                )}

              </button>

            )
          )}

        </div>

      )}

    </div>

  );
}


export default ThemeSelector;