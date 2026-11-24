// Мини-i18n: семантические SCREAMING_SNAKE_CASE-ключи, словари RU/EN в
// locales.ts. Язык: settings.json бэкенда (поле lang в /api/state —
// резолвленное "ru"|"en"), localStorage — зеркало для первого кадра
// до ответа API.
import { useEffect, useState } from "react";
import { uiSetting, setUiSetting } from "./settings";
import { RU, EN } from "./locales";

export type Lang = "ru" | "en";

const guess: Lang = uiSetting<Lang>(
  "lang",
  navigator.language?.toLowerCase().startsWith("ru") ? "ru" : "en",
);
let cur: Lang = guess === "ru" ? "ru" : "en";
const subs = new Set<() => void>();

export function getLang() {
  return cur;
}

export function setLang(l: Lang) {
  if (l === cur) return;
  cur = l;
  setUiSetting("lang", l);
  subs.forEach((f) => f());
}

/** Подписка на смену языка — компоненты, рисующие t(), должны её звать. */
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

// Русские плюрали: значение "один|несколько|много" выбирается по vars.n.
const plIdx = (n: number) =>
  n % 10 === 1 && n % 100 !== 11
    ? 0
    : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)
      ? 1
      : 2;

export function t(key: string, vars?: Record<string, string | number>): string {
  const dict = cur === "en" ? EN : RU;
  let out = dict[key] ?? EN[key] ?? key;
  if (out.includes("|") && typeof vars?.n === "number") {
    const parts = out.split("|");
    out = parts[plIdx(vars.n)] ?? parts[0];
  }
  return vars
    ? out.replace(/\{(\w+)\}/g, (m, k) => String(vars[k] ?? m))
    : out;
}

/** t() + подписка на смену языка для ре-рендера. */
export function useT() {
  useLang();
  return t;
}

export function localeTag() {
  return cur === "ru" ? "ru-RU" : "en-US";
}
