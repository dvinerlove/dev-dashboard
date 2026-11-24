import { useSyncExternalStore } from "react";
import { api, type DashState } from "./api";

let state: DashState | null = null;
const subs = new Set<() => void>();
let timer: number | undefined;

// optimistic UI: name -> ожидаемый state; снимается на следующем тике или по таймауту
const pend = new Map<string, string>();

export function markPending(name: string, expect: "up" | "down") {
  pend.set(name, expect);
  subs.forEach((f) => f());
  setTimeout(() => {
    if (pend.delete(name)) subs.forEach((f) => f());
  }, 10000);
}

/** Хук: ожидаемый state сервиса/проекта во время действия (optimistic). */
export function usePending(name: string): "up" | "down" | undefined {
  return useSyncExternalStore(
    (cb) => {
      subs.add(cb);
      return () => subs.delete(cb);
    },
    () => pend.get(name) as "up" | "down" | undefined,
  );
}

let inflight = false;

// история RAM (последние 30 тиков) для спарклайна инспектора
const ramHist = new Map<string, number[]>();
const RAM_KEEP = 30;
/** Точки спарклайна RAM по имени строки (старейшая → новейшая). */
export const ramHistory = (n: string): number[] => ramHist.get(n) ?? [];

async function tick() {
  if (inflight) return; // старый ответ не должен перезаписать новый
  inflight = true;
  try {
    state = await api.state();
    if (state) {
      const rows = [...state.services, ...state.remotes, ...state.projects];
      // pending снимается, как только реальное состояние догнало ожидание
      if (pend.size)
        for (const [n, want] of pend)
          if (rows.find((r) => r.name === n)?.state === want)
            pend.delete(n);
      for (const r of rows) {
        if (r.m?.mb == null) continue;
        const h = ramHist.get(r.name) ?? [];
        h.push(r.m.mb);
        if (h.length > RAM_KEEP) h.splice(0, h.length - RAM_KEEP);
        ramHist.set(r.name, h);
      }
      for (const k of [...ramHist.keys()])
        if (!rows.some((r) => r.name === k)) ramHist.delete(k);
    }
  } catch {
    /* API ещё не поднялся — повторит интервал */
  } finally {
    inflight = false;
  }
  subs.forEach((f) => f());
}

export function refresh() {
  return tick();
}

export function startPolling(ms = 2000) {
  tick();
  timer = window.setInterval(tick, ms);
  return () => window.clearInterval(timer);
}

/** Текущий state вне React — для акций, которым не нужна подписка. */
export const getDash = () => state;

export function useDash(): DashState | null {
  return useSyncExternalStore(
    (cb) => {
      subs.add(cb);
      return () => subs.delete(cb);
    },
    () => state,
  );
}
