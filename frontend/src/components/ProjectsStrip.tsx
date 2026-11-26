import { useEffect, useState } from "react";
import type { ScannedProject } from "../lib/api";
import { api, projectToSpec } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { cn } from "../lib/utils";
import { refresh, useCached, useDash } from "../lib/store";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ChevronDown, Search } from "lucide-react";
import { toast } from "sonner";

// scanned folders live in the view, not a dialog — same ambient-discovery
// pattern as CandidatesStrip. Row click → prefilled "new project" dialog;
// checkboxes keep the old bulk-add flow. One container for both states:
// the list reveals through a grid-rows transition instead of teleporting.
export function ProjectsStrip() {
  const t = useT();
  const app = useApp();
  const st = useDash();
  const [list, setList] = useCached<ScannedProject[]>("scan-projects");
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [root, setRoot] = useState(""); // '' = all roots
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const norm = (s: string) =>
    s.replaceAll("/", "\\").replace(/\\+$/, "").toLowerCase();
  const load = () =>
    api
      .scan()
      .then((r) => {
        setList(r.found);
        setChecked(new Set(r.found.map((p) => p.cwd)));
      })
      .catch(() => setList([]));
  useEffect(() => {
    load();
  }, []);
  // fresh scan on every expand
  useEffect(() => {
    if (open) load();
  }, [open]);

  // saved/deleted elsewhere → the strip self-heals off the live store
  const own = new Set(
    (st?.projects ?? []).map((p) => norm(p.cwd ?? "")),
  );
  const live = (list ?? []).filter((p) => !own.has(norm(p.cwd)));
  // hidden only once loaded-and-empty — hiding during the loading pass
  // unmounts the shimmer with it, leaving seconds of dead nothing on cold scans
  if (list !== null && !live.length) return null;
  const roots = [
    ...new Set(live.map((p) => p.root).filter((r): r is string => !!r)),
  ];
  const inRoot = root ? live.filter((p) => p.root === root) : live;
  const lq = q.trim().toLowerCase();
  const rows = lq
    ? inRoot.filter((p) =>
        [p.name, p.cwd, p.cmd, p.url ?? "", p.framework ?? "", p.branch ?? ""]
          .join(" ")
          .toLowerCase()
          .includes(lq),
      )
    : inRoot;
  const base = (r: string) =>
    r.replace(/[\\/]+$/, "").split(/[\\/]/).pop() || r;
  const toggle = (cwd: string) =>
    setChecked((s) => {
      const n = new Set(s);
      if (n.has(cwd)) n.delete(cwd);
      else n.add(cwd);
      return n;
    });
  // add what you see: the button counts only the rows on screen
  const picked = rows.filter((p) => checked.has(p.cwd));
  const addChecked = () => {
    api.addProjects(picked).then((r) => {
      if (!r.ok) return toast(r.msg || t("ERROR"));
      toast(t("ADDED_COUNT", { n: picked.length }));
      setChecked(new Set());
      load(); // rescan — removes added rows, reveals newly deleted ones
      refresh();
    });
  };
  const pick = (p: ScannedProject) =>
    app.openDlg({ t: "project", spec: projectToSpec(p), isNew: true });

  return (
    <div className="mb-2 rounded-md border border-(--border-hairline) bg-(--bg-surface)/40">
      <div className="flex items-center gap-1.5 pr-1.5">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          disabled={list === null}
          aria-expanded={open}
          aria-busy={list === null || undefined}
          aria-controls="scan-list"
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
            {t("FOUND_PROJECTS")}
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
              {`· ${live.length}`}
              {!open &&
                ` ${live
                    .slice(0, 5)
                    .map((p) => p.name)
                    .join(", ")}${live.length > 5 ? "…" : ""}`}
            </span>
          )}
        </button>
        {open && picked.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-5 shrink-0 px-1.5 text-[10.5px]"
            onClick={addChecked}
          >
            {t("ADD_COUNT", { n: picked.length })}
          </Button>
        )}
        {open && live.length > 4 && (
          <div className="relative shrink-0">
            <Search className="pointer-events-none absolute left-1.5 top-1/2 h-3 w-3 -translate-y-1/2 text-(--text-muted)" />
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("PROJECT_SEARCH_PLACEHOLDER")}
              aria-label={t("PROJECT_SEARCH_PLACEHOLDER")}
              className="h-6 w-40 border-(--border-hairline) bg-(--bg-canvas) pl-6 text-[11px]"
            />
          </div>
        )}
      </div>
      <div
        id="scan-list"
        className={cn(
          "grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        )}
      >
        <div className="min-h-0 overflow-hidden">
          {list !== null && roots.length > 1 && (
            <div className="flex flex-wrap items-center gap-1 px-1.5 pb-1">
              {["", ...roots].map((r) => (
                <button
                  type="button"
                  key={r || "__all"}
                  aria-pressed={root === r}
                  onClick={() => setRoot(r)}
                  className={cn(
                    "h-5 cursor-pointer rounded-md px-1.5 font-mono text-[10.5px] transition-colors",
                    root === r
                      ? "bg-(--bg-selected) text-(--text-primary)"
                      : "text-(--text-muted) hover:text-(--text-secondary)",
                  )}
                >
                  {r ? base(r) : t("ALL")}
                  <span className="ml-1 text-[9.5px] text-(--text-muted)">
                    {r
                      ? live.filter((p) => p.root === r).length
                      : live.length}
                  </span>
                </button>
              ))}
            </div>
          )}
          <ul
            className="max-h-[260px] overflow-y-auto overscroll-contain"
          >
            {(list ? rows : []).map((p) => (
              <li key={p.cwd}>
                <div className="flex items-center gap-2 rounded px-1.5 py-1">
                  <input
                    type="checkbox"
                    checked={checked.has(p.cwd)}
                    onChange={() => toggle(p.cwd)}
                    aria-label={p.name}
                    className="accent-(--accent)"
                  />
                  <button
                    type="button"
                    onClick={() => pick(p)}
                    title={t("NEW_PROJECT")}
                    className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 rounded px-0.5 text-left transition-colors hover:bg-(--bg-hover)"
                  >
                    <span
                      role="img"
                      aria-label={t(
                        p.running ? "STATE_RUNNING" : "WHY_STOPPED",
                      )}
                      title={t(p.running ? "STATE_RUNNING" : "WHY_STOPPED")}
                      className={cn(
                        "h-1.5 w-1.5 shrink-0 rounded-full",
                        p.running
                          ? "bg-(--status-green)"
                          : "border border-(--text-muted)",
                      )}
                    />
                    <span className="min-w-0">
                      <span className="flex items-center gap-1.5 truncate text-[12px] font-medium text-(--text-primary)">
                        <span className="truncate">{p.name}</span>
                        {p.framework && (
                          <span className="shrink-0 text-[10px] font-normal text-(--text-muted)">
                            {p.framework}
                          </span>
                        )}
                        {p.branch && (
                          <span className="shrink-0 font-mono text-[10px] font-normal text-(--text-muted)">
                            ⎇ {p.branch}
                          </span>
                        )}
                        {/* a chip per sibling worktree checkout of the repo —
                            primary's own checkout already shows as p.branch */}
                        {p.worktrees
                          ?.filter((w) => norm(w.cwd) !== norm(p.cwd))
                          .map((w) => (
                            <span
                              key={w.cwd}
                              title={w.cwd}
                              className="shrink-0 font-mono text-[10px] font-normal text-(--text-muted)"
                            >
                              ⎇ {w.branch || base(w.cwd)}
                            </span>
                          ))}
                        {p.restored && (
                          <span className="shrink-0 text-[9.5px] font-normal text-(--accent)">
                            · {t("WHY_DELETED")}
                          </span>
                        )}
                        {(p.env_open || p.env_committed) && (
                          <span
                            title={t("ENV_IN_GIT_TIP")}
                            className="shrink-0 rounded bg-(--status-red)/20 px-1 py-px text-[9.5px] font-medium text-(--status-red)"
                          >
                            {t("ENV_IN_GIT")}
                          </span>
                        )}
                        {!!p.env_missing?.length && (
                          <span
                            title={t("ENV_MISSING_TIP", {
                              list: p.env_missing.join(", "),
                            })}
                            className="shrink-0 rounded bg-(--status-amber)/20 px-1 py-px text-[9.5px] font-medium text-(--status-amber)"
                          >
                            {p.env_missing.length === 1
                              ? t("MISSING_NAME", {
                                  name: p.env_missing[0],
                                })
                              : t("MISSING_ENV_COUNT", {
                                  n: p.env_missing.length,
                                })}
                          </span>
                        )}
                      </span>
                      <span className="block truncate font-mono text-[10.5px] text-(--text-muted)">
                        {p.cwd}
                        <span className="text-(--text-secondary)">
                          {" · "}
                          {p.cmd}
                        </span>
                      </span>
                    </span>
                  </button>
                  {/* one chip per compose service → "new project" dialog
                      prefilled with `docker compose up <svc>` */}
                  {p.compose_services?.map((svc) => (
                    <button
                      key={svc}
                      type="button"
                      title={`docker compose up ${svc}`}
                      onClick={() =>
                        app.openDlg({
                          t: "project",
                          spec: {
                            name: `${p.name}·${svc}`,
                            cmd: `docker compose up ${svc}`,
                            cwd: p.cwd,
                          },
                          isNew: true,
                        })
                      }
                      className="shrink-0 cursor-pointer rounded bg-(--bg-hover) px-1 py-px font-mono text-[9.5px] text-(--text-secondary) transition-colors hover:bg-(--bg-selected) hover:text-(--text-primary)"
                    >
                      {svc}
                    </button>
                  ))}
                </div>
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
