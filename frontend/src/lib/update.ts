// Update check state: the GitHub latest-release lookup is shared between the
// passive startup check, the topbar icon and the manual button in settings.
import { useSyncExternalStore } from "react";
import { toast } from "sonner";
import { api } from "./api";
import { t } from "./i18n";

export interface UpdateInfo {
  tag: string;
  url: string;
}

/** Numeric semver-ish compare: is `tag` newer than `cur`? */
export function isNewer(cur: string, tag: string): boolean {
  const a = cur.split(".").map((x) => parseInt(x, 10) || 0);
  const b = tag.split(".").map((x) => parseInt(x, 10) || 0);
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const d = (b[i] ?? 0) - (a[i] ?? 0);
    if (d) return d > 0;
  }
  return false;
}

/** Latest GitHub release; throws on network/shape errors. */
export async function fetchLatestRelease(): Promise<UpdateInfo> {
  const r = await fetch(
    "https://api.github.com/repos/dvinerlove/dev-dashboard/releases/latest",
    { signal: AbortSignal.timeout(8000) },
  );
  if (!r.ok) throw new Error(`${r.status}`);
  const j = (await r.json()) as { tag_name?: string; html_url?: string };
  const tag = String(j.tag_name ?? "").replace(/^v/, "");
  if (!tag || !j.html_url) throw new Error("bad release");
  return { tag, url: j.html_url };
}

let info: UpdateInfo | null = null;
const subs = new Set<() => void>();

export function setUpdateInfo(v: UpdateInfo | null) {
  info = v;
  subs.forEach((f) => f());
}

export const getUpdateInfo = () => info;

/** Newer release found this session (by the startup check or manually). */
export function useUpdateInfo(): UpdateInfo | null {
  return useSyncExternalStore(
    (cb) => {
      subs.add(cb);
      return () => subs.delete(cb);
    },
    () => info,
  );
}

// passive startup check: one fetch per session, silent on any failure —
// no network / rate limit / no newer release all look the same
let checked = false;
export function startupUpdateCheck(version: string) {
  if (checked || !version) return;
  checked = true;
  fetchLatestRelease()
    .then((rel) => {
      if (isNewer(version, rel.tag)) setUpdateInfo(rel);
    })
    .catch(() => {});
}

/** self-update + toasts; true when the app is about to restart. */
export async function installUpdate(): Promise<boolean> {
  const r = await api.selfUpdate().catch(() => null);
  if (r?.ok) {
    toast(t("UPDATE_RESTARTING"));
    // the app exits and relaunches itself — nothing more to do
    return true;
  }
  toast.error(r?.msg || t("UPDATE_FAILED"));
  return false;
}
