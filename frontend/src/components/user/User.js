import { useEffect, useState } from "react";
import { connect } from "react-redux";
import { useNavigate } from "react-router";
import moment from "moment";
import "../../css/User.css";
import DelUserModal from "./DelUserModal";
import ErrorAlert from "../ErrorAlert";
import { useTranslation } from "react-i18next";
import { updateUserOptions } from "../../actions/authActions";
import { applyThemeToDocument } from "../../utils/themeUtils";

const themeOptions = [
  { value: 0, label: "Nocturne" },
  { value: 1, label: "Ocean" },
  { value: 2, label: "Violet" },
  { value: 3, label: "Light" },
];

const languageOptions = [
  { value: "en", label: "English" },
  { value: "et", label: "Eesti" },
];

const User = ({ auth, err, updateUserOptions }) => {
  const { t } = useTranslation();
  const [showModal, setShowModal] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState(
    auth?.user?.options?.theme ?? 0,
  );
  const [selectedLanguage, setSelectedLanguage] = useState(
    auth?.user?.options?.localization || "en",
  );
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const { user } = auth;
  let navigate = useNavigate();

  useEffect(() => {
    const storedTheme = auth?.user?.options?.theme ?? 0;
    const storedLocalization = auth?.user?.options?.localization || "en";
    setSelectedTheme(storedTheme);
    setSelectedLanguage(storedLocalization);
    applyThemeToDocument(storedTheme);
  }, [auth?.user?.options?.theme, auth?.user?.options?.localization]);

  const handleOptionsChange = async () => {
    if (!auth.isAuthenticated) return;

    const data = {
      theme: Number(selectedTheme),
      localization: selectedLanguage,
    };

    setIsSaving(true);
    setSaveMessage("");

    try {
      await updateUserOptions(data);
      setSaveMessage(t("Saved successfully"));
    } catch (error) {
      setSaveMessage(t("Could not save changes"));
    } finally {
      setIsSaving(false);
    }
  };
  // refresh data after options update
  useEffect(() => {}, [auth?.user?.options]);

  useEffect(() => {
    !auth.isAuthenticated && navigate("/");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.isAuthenticated]);

  return (
    <div className="container">
      <div className="user-content">
        {err.id === "DEL_USER_ERROR" && <ErrorAlert />}
        <div className="user-header">
          <h3>{t("User settings")}</h3>
          <button
            type="button"
            className="user-close-button"
            onClick={() => navigate("/")}
          >
            {t("Close")}
          </button>
        </div>
        <ul className="user-data">
          <h4>{t("User data")}:</h4>
          <li>
            {t("Name")}: {user?.first_name && user.first_name}{" "}
            {user?.last_name && user.last_name}
          </li>
          <li>
            {t("Email")}: {user?.email}
          </li>
          <li>
            {t("Account created")}: {moment(user?.created_at).format("lll")}
          </li>
          <li>
            {t("Account updated")}: {moment(user?.updated_at).format("lll")}
          </li>
        </ul>
        <ul className="user-options">
          <h4 className="user-section-title">{t("User options")}:</h4>
          <li className="settings-card">
            <div className="settings-row">
              <label htmlFor="theme-select">{t("Theme")}</label>
              <select
                id="theme-select"
                className="theme-select"
                value={selectedTheme}
                onChange={(event) => {
                  const nextTheme = Number(event.target.value);
                  setSelectedTheme(nextTheme);
                  applyThemeToDocument(nextTheme);
                }}
              >
                {themeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="settings-row">
              <label htmlFor="language-select">{t("Language")}</label>
              <select
                id="language-select"
                className="theme-select"
                value={selectedLanguage}
                onChange={(event) => {
                  setSelectedLanguage(event.target.value);
                }}
              >
                {languageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="settings-actions">
              <button
                type="button"
                className="save-button"
                onClick={handleOptionsChange}
                disabled={isSaving}
              >
                {isSaving ? t("Saving...") : t("Save changes")}
              </button>
              {saveMessage && (
                <span className="save-feedback">{saveMessage}</span>
              )}
            </div>
          </li>
        </ul>
        <div className="user-delete">
          <button
            className="btn"
            onClick={() => {
              setShowModal(true);
            }}
          >
            {t("Delete account")}
          </button>
        </div>
        <DelUserModal setShowModal={setShowModal} showModal={showModal} />
      </div>
    </div>
  );
};

const mapStateToProps = (state) => ({
  auth: state.auth,
  err: state.error,
});

export default connect(mapStateToProps, { updateUserOptions })(User);
