const THEME_OPTIONS = {
  0: "0",
  1: "1",
  2: "2",
  3: "3",
};

const THEME_NAME_TO_ID = {
  nocturne: "0",
  ocean: "1",
  violet: "2",
  light: "3",
};

export const getThemeName = (themeValue) => {
  if (themeValue === null || themeValue === undefined) {
    return THEME_OPTIONS[0];
  }

  if (typeof themeValue === "string") {
    const normalizedValue = themeValue.trim().toLowerCase();
    if (THEME_NAME_TO_ID[normalizedValue]) {
      return THEME_NAME_TO_ID[normalizedValue];
    }

    const numericValue = Number(normalizedValue);
    return THEME_OPTIONS[numericValue] || THEME_OPTIONS[0];
  }

  const normalizedValue = Number(themeValue);
  return THEME_OPTIONS[normalizedValue] || THEME_OPTIONS[0];
};

export const applyThemeToDocument = (themeValue) => {
  const themeName = getThemeName(themeValue);
  document.documentElement.setAttribute("data-theme", themeName);
  return themeName;
};

export const getThemeValueFromName = (themeName) => {
  const normalizedTheme = String(themeName).trim().toLowerCase();
  if (THEME_NAME_TO_ID[normalizedTheme]) {
    return Number(THEME_NAME_TO_ID[normalizedTheme]);
  }

  return Number(normalizedTheme) || 0;
};
