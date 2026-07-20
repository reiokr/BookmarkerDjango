import { applyThemeToDocument } from "./themeUtils";

describe("theme utilities", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
  });

  it("applies a supported theme to the document root", () => {
    applyThemeToDocument(2);

    expect(document.documentElement.getAttribute("data-theme")).toBe("2");
  });

  it("falls back to the default theme for unsupported values", () => {
    applyThemeToDocument("mystery");

    expect(document.documentElement.getAttribute("data-theme")).toBe("0");
  });
});
