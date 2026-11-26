import { useEffect, useState } from "react";
import type { ServiceCandidate } from "../lib/api";
import { api, candidateToSpec } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useCached } from "../lib/store";
import { cn } from "../lib/utils";
import { Input } from "./ui/input";
import { ChevronDown, Search } from "lucide-react";

// zombie reason → locale key (backend raw values, do not translate upstream)
const ZOMBIE_WHY: Record<string, string> = {
  cwd_missing: "ZOMBIE_CWD_MISSING",
  parent_dead: "ZOMBIE_PARENT_DEAD",
  aged: "ZOMBIE_AGED",
};

// detected candidates live in the view, not the dialog: discovery is
// ambient — the strip sits next to the table its picks will land in.
// One container for both states: the list reveals through a
// grid-rows transition instead of teleporting.
export function CandidatesStrip() {
  const t = useT();
  const app = useApp();
  const [list, setList] = useCached<ServiceCandidate[]>("svc-candidates");
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  useEffect(() => {
    api.serviceCandidates().then(setList).catch(() => setList([]));
  }, []);
  useEffect(() => {
    if (open) api.serviceCandidates().then(setList).catch(() => {});
  }, [open]);
  const cid = "cand-list";
  // same as ProjectsStrip: hidden only once loaded-and-empty,
  // the loading pass keeps the strip so the shimmer can render
  if (list !== null && !list.length) return null;
  const lq = q.trim().toLowerCase();
  const rows = lq
    ? (list ?? []).filter((c) =>
        [c.name, c.label, c.proc, c.match, c.ports.join(" ")]
          .join(" ")
          .toLowerCase()
          .includes(lq),
      )
    : (list ?? []);
  const pick = (c: ServiceCandidate) =>
    app.openDlg({ t: "service", spec: candidateToSpec(c), isNew: true });
  return (
    <div className="mb-2 rounded-md border border-(--border-hairline) bg-(--bg-surface)/40">
      <div className="flex items-center gap-1.5 pr-1.5">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          disabled={list === null}
          aria-expanded={open}
          aria-busy={list === null || undefined}
          aria-controls={cid}
          className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left text-[11px] text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--text-secondary) disabled:cursor-default disabled:hover:bg-transparent disabled:hover:text-(--text-muted)"
        >
          <ChevronDown
            className={cn(
              "h-3 w-3 shrink-0 transition-transform duration-200 motion-reduce:transition-none",
              !open && "-rotate-90",
            )}
            aria-hidden
          />
          <span className="shrink-0 uppercase tracking-wider">
            {t("DETECTED_RUNNING")}
          </span>
          {/* the bar exists from frame 0; only this slot changes —
              shimmer fades into the count+names via overlay-in */}
          {list === null ? (
            <span
              className="h-3 min-w-0 flex-1 animate-pulse rounded bg-(--bg-hover)"
              aria-hidden
            />
          ) : (
            <span className="min-w-0 flex-1 animate-[overlay-in_140ms_ease-out] truncate">
              {`· ${list.length}`}
              {!open &&
                ` ${list
                    .slice(0, 5)
                    .map((c) => c.name)
                    .join(", ")}${list.length > 5 ? "…" : ""}`}
            </span>
          )}
        </button>
        {open && (list?.length ?? 0) > 4 && (
          <div className="relative shrink-0">
            <Search className="pointer-events-none absolute left-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-(--text-muted)" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("PORT_SEARCH_PLACEHOLDER")}
              aria-label={t("PORT_SEARCH_PLACEHOLDER")}
              className="h-6 w-40 border-(--border-hairline) bg-(--bg-canvas) pl-6 text-[11px]"
            />
          </div>
        )}
      </div>
      <div
        id={cid}
        className={cn(
          "grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        )}
      >
        <div className="min-h-0 overflow-hidden">
          <ul
            className="max-h-[220px] overflow-y-auto overscroll-contain"
          >
            {rows.map((c) => (
              <li key={c.name + "-" + c.pid}>
                <button
                  type="button"
                  onClick={() => pick(c)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-1.5 py-1 text-left transition-colors hover:bg-(--bg-hover)"
                >
                  <span
                    role="img"
                    aria-label={t(
                      c.alive === false ? "WHY_STOPPED" : "STATE_RUNNING",
                    )}
                    title={t(
                      c.alive === false ? "WHY_STOPPED" : "STATE_RUNNING",
                    )}
                    className={cn(
                      "h-1.5 w-1.5 shrink-0 rounded-full",
                      c.alive === false
                        ? "border border-(--text-muted)"
                        : "bg-(--status-green)",
                    )}
                  />
                  <span
                    title={c.name}
                    className={cn(
                      "truncate text-[12px] font-medium",
                      c.alive === false
                        ? "text-(--text-muted)"
                        : "text-(--text-primary)",
                    )}
                  >
                    {c.name}
                  </span>
                  <span
                    title={c.label || c.proc}
                    className="min-w-0 truncate text-[10.5px] text-(--text-muted)"
                  >
                    {c.label || c.proc}
                    {(c.why ?? [])
                      .filter((w) => w !== "WHY_STOPPED")
                      .map((w) => (
                        <span
                          key={w}
                          className={
                            w === "WHY_DELETED" ? "text-(--accent)" : ""
                          }
                        >
                          {" · "}
                          {t(w)}
                        </span>
                      ))}
                  </span>
                  {c.zombie && (
                    <span
                      title={t(ZOMBIE_WHY[c.zombie] ?? "ZOMBIE")}
                      className="shrink-0 rounded bg-(--status-amber)/20 px-1 text-[9.5px] font-medium text-(--status-amber)"
                    >
                      {t("ZOMBIE")}
                    </span>
                  )}
                  {c.agent && (
                    <span
                      title={t("AGENT_LAUNCHED", { agent: c.agent })}
                      className="shrink-0 font-mono text-[10px] text-(--text-muted)"
                    >
                      {c.agent}
                    </span>
                  )}
                  <span className="ml-auto shrink-0 font-mono text-[10.5px] text-(--text-secondary)">
                    {c.ports.map((p) => `:${p}`).join(" ")}
                  </span>
                </button>
              </li>
            ))}
            {lq && !rows.length && (
              <li className="px-1.5 py-1 text-[11px] text-(--text-muted)">
                {t("NOTHING_FOUND")}
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
