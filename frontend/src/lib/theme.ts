export type ThemeId = "graphite" | "console" | "paper" | "paperdark1" | "paperdark2" | "retro";

export const THEMES: { id: ThemeId; label: string }[] = [
  { id: "graphite", label: "THEME_GRAPHITE" },
  { id: "console", label: "THEME_CONSOLE" },
  { id: "paper", label: "THEME_PAPER" },
  { id: "paperdark1", label: "THEME_PAPER_MIDNIGHT" },
  { id: "paperdark2", label: "THEME_PAPER_ESPRESSO" },
  { id: "retro", label: "THEME_RETRO" },
];

const KEY = "dd-theme";

/** --bg-base каждой темы: фон окна/WebView2 под текущую тему,
   чтобы полоса при ресайзе и вспышка при загрузке сливались */
const THEME_BG: Record<ThemeId, string> = {
  graphite: "#0B0D11",
  console: "#050905",
  paper: "#EDEBE5",
  paperdark1: "#171512",
  paperdark2: "#100E0B",
  retro: "#C0C0C0",
};

/** Цвета для мини-превью тем (свотчи в онбординге) — близкие
   к токенам index.css: фон, поверхность, акцент, текст */
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

/** до первого рендера — без вспышки дефолтной темы */
export function initTheme(): ThemeId {
  const t = currentTheme();
  document.documentElement.dataset.theme = t;
  // мост ещё не готов — досинхронизируем фон по pywebviewready
  window.addEventListener("pywebviewready", () => syncNativeBg(t), {
    once: true,
  });
  return t;
}
