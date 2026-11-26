export type ThemeId = "graphite" | "console" | "paper" | "paperdark1" | "paperdark2" | "retro";

export const THEMES: { id: ThemeId; label: string }[] = [
  { id: "paper", label: "THEME_PAPER" },
  { id: "paperdark1", label: "THEME_PAPER_MIDNIGHT" },
  { id: "paperdark2", label: "THEME_PAPER_ESPRESSO" },
  { id: "graphite", label: "THEME_GRAPHITE" },
  { id: "console", label: "THEME_CONSOLE" },
  { id: "retro", label: "THEME_RETRO" },
];

const KEY = "dd-theme";

/** --bg-base of each theme: window/WebView2 background matching the theme
   so the resize stripe and the load flash blend in */
const THEME_BG: Record<ThemeId, string> = {
  graphite: "#0B0D11",
  console: "#050905",
  paper: "#EDEBE5",
  paperdark1: "#171512",
  paperdark2: "#100E0B",
  retro: "#C0C0C0",
};

/** Colors for theme mini-previews (swatches in onboarding) — close
   to the index.css tokens: background, surface, accent, text */
export const THEME_SWATCH: Record<
  ThemeId,
  { bg: string; surface: string; accent: string; text: string }
> = {
  graphite: { bg: "#0B0D11", surface: "#161A22", accent: "#5E81F4", text: "#ECEFF4" },
  console: { bg: "#050905", surface: "#0B150B", accent: "#4ADE80", text: "#D9F2DC" },
  paper: { bg: "#EDEBE5", surface: "#FFFFFF", accent: "#4F46E5", text: "#20242D" },
  paperdark1: { bg: "#171512", surface: "#24211B", accent: "#6C63F0", text: "#EBE7DB" },
  paperdark2: { bg: "#100E0B", surface: "#1C1813", accent: "#7A72F5", text: "#EFE9DC" },
  retro: { bg: "#C0C0C0", surface: "#FFFFFF", accent: "#000080", text: "#000000" },
};

export function syncNativeBg(t = currentTheme()) {
  (
    window as unknown as {
      pywebview?: { api?: { window_set_bg?: (c: string) => void } };
    }
  ).pywebview?.api?.window_set_bg?.(THEME_BG[t]);
}

export function currentTheme(): ThemeId {
  const t = localStorage.getItem(KEY) as ThemeId | null;
  return t && THEMES.some((x) => x.id === t) ? t : "graphite";
}

export function applyTheme(t: ThemeId) {
  document.documentElement.dataset.theme = t;
  localStorage.setItem(KEY, t);
  syncNativeBg(t);
}

/** until the first render — no default-theme flash */
export function initTheme(): ThemeId {
  const t = currentTheme();
  document.documentElement.dataset.theme = t;
  // bridge not ready — resync the background on pywebviewready
  window.addEventListener("pywebviewready", () => syncNativeBg(t), {
    once: true,
  });
  return t;
}
