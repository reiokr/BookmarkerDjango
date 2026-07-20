import { useEffect, useRef, useState } from "react";
import i18next from "i18next";
import TranslateOutlinedIcon from "@mui/icons-material/TranslateOutlined";
import { useTranslation } from "react-i18next";
import { languages } from "./lang";

const LocaleButton = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const currentLanguageCode = localStorage.getItem("i18nextLng") || "en";
  const currentLanguage = languages.find((l) => l.code === currentLanguageCode);
  const { t } = useTranslation();

  useEffect(() => {
    document.body.dir = currentLanguage.dir || "ltr";
    document.title = t("app_title");
  }, [currentLanguage, t]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLanguageChange = (code) => {
    i18next.changeLanguage(code);
    setIsOpen(false);
  };

  return (
    <div className="dropdown" ref={dropdownRef}>
      <button
        className={`dropbtn${isOpen ? " active" : ""}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-label="Select language"
      >
        <TranslateOutlinedIcon />
      </button>
      <div className={`dropdown-content${isOpen ? " show" : ""}`}>
        {languages.map(({ code, name, country_code }) => {
          const isActive = currentLanguageCode === code;

          return (
            <div
              key={country_code}
              className={`locale-option${isActive ? " active" : ""}`}
              onClick={() => handleLanguageChange(code)}
            >
              <span
                className={`flag-icon flag-icon-${country_code} mx-2`}
                style={{
                  opacity: isActive ? 0.7 : 1,
                }}
              ></span>
              <span>{name}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LocaleButton;
