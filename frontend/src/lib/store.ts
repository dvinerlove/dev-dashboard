import { useState, useSyncExternalStore } from "react";
import { api, type DashState } from "./api";

let state: DashState | null = null;
const subs = new Set<() => void>();
let timer: number | undefined;

// optimistic UI: name -> expected state; cleared on the next tick or by timeout
const pend = new Map<string, string>();

export function markPending(name: string, expect: "up" | "down") {
  pend.set(name, expect);
  subs.forEach((f) => f());
  setTimeout(() => {
    if (pend.delete(name)) subs.forEach((f) => f());
  }, 10000);
}

/** Hook: expected service/project state during an action (optimistic). */
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

// RAM history (last 30 ticks) for the inspector sparkline
const ramHist = new Map<string, number[]>();
const RAM_KEEP = 30;
/** RAM sparkline points by row name (oldest → newest). */
export const ramHistory = (n: string): number[] => ramHist.get(n) ?? [];

async function tick() {
  if (inflight) return; // a stale response must not overwrite a newer one
  inflight = true;
  try {
    state = await api.state();
    if (state) {
      const rows = [...state.services, ...state.remotes, ...state.projects];
      // pending clears once the real state catches up with the expected
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
    /* API not up yet — retries the interval */
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

/** Current state outside React — for actions that need no subscription. */
export const getDash = () => state;

// stale-while-revalidate for per-view GETs: a remount renders the last
// response instantly, the refetch silently replaces it — no skeleton flash
const viewCache = new Map<string, unknown>();

// persisted across restarts: strips render warm data from frame 0 and
// self-heal when the rescan lands. shortcut: shape-drift guard only —
// bump CACHE_VER when a cached payload changes shape incompatibly
const CACHE_VER = 1;

export function useCached<T>(key: string): [T | null, (v: T) => void] {
  const [v, setV] = useState<T | null>(() => {
    const mem = (viewCache.get(key) as T) ?? null;
    if (mem !== null) return mem;
    try {
      const raw = localStorage.getItem(`vcache:${key}`);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed?.v === CACHE_VER) return parsed.data as T;
      }
    } catch {
      /* corrupted or unavailable — cold start */
    }
    return null;
  });
  const set = (nv: T) => {
    viewCache.set(key, nv);
    try {
      localStorage.setItem(
        `vcache:${key}`,
        JSON.stringify({ v: CACHE_VER, data: nv }),
      );
    } catch {
      /* quota/serialization — cache is best-effort */
    }
    setV(nv);
  };
  return [v, set];
}

export function useDash(): DashState | null {
  return useSyncExternalStore(
    (cb) => {
      subs.add(cb);
      return () => subs.delete(cb);
    },
    () => state,
  );
}
