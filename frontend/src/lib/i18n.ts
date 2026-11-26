// Mini-i18n: semantic SCREAMING_SNAKE_CASE keys, one file per language in the
// root locales/<lang>.json — adding a language = dropping a file, no code
// changes. Miss → en → the key itself. Language: backend settings.json
// (the resolved lang field in /api/state), localStorage is a mirror for the
// first frame before the API answers.
import { useEffect, useState } from "react";
import { uiSetting, setUiSetting } from "./settings";

const files = import.meta.glob<Record<string, unknown>>(
  "../../../locales/*.json",
  { eager: true, import: "default" },
);
export const LOCALES: Record<string, Record<string, unknown>> = {};
for (const [p, dict] of Object.entries(files))
  LOCALES[p.slice(p.lastIndexOf("/") + 1, -5)] = dict;

export type Lang = string;
export const LANGS = Object.keys(LOCALES).sort();

const guess = uiSetting<string>(
  "lang",
  (navigator.language ?? "en").toLowerCase().split("-")[0],
);
let cur: Lang = LOCALES[guess] ? guess : "en";
const subs = new Set<() => void>();

export function getLang() {
  return cur;
}

export function setLang(l: Lang) {
  if (l === cur || !LOCALES[l]) return;
  cur = l;
  setUiSetting("lang", l);
  subs.forEach((f) => f());
}

/** Language-change subscription — components that render t() must call it. */
export function useLang(): Lang {
  const [l, setL] = useState(cur);
  useEffect(() => {
    const f = () => setL(cur);
    subs.add(f);
    return () => {
      subs.delete(f);
    };
  }, []);
  return l;
}

// Russian plurals: the "one|few|many" value is picked by vars.n.
const plIdx = (n: number) =>
  n % 10 === 1 && n % 100 !== 11
    ? 0
    : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)
      ? 1
      : 2;

export function t(key: string, vars?: Record<string, string | number>): string {
  // server/detail/tpl sections are objects; find picks the first string: locale → en → key
  let out = [LOCALES[cur]?.[key], LOCALES.en?.[key], key].find(
    (v): v is string => typeof v === "string",
  )!;
  if (out.includes("|") && typeof vars?.n === "number") {
    const parts = out.split("|");
    out = parts[plIdx(vars.n)] ?? parts[0];
  }
  return vars
    ? out.replace(/\{(\w+)\}/g, (m, k) => String(vars[k] ?? m))
    : out;
}

/** t() + language-change subscription for re-render. */
export function useT() {
  useLang();
  return t;
}

export function localeTag() {
  return cur === "ru" ? "ru-RU" : cur === "en" ? "en-US" : cur;
}
