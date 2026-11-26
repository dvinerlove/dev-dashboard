import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ChevronLeft,
  ChevronRight,
  Command,
  FolderOpen,
  FolderPlus,
  Loader2,
  PanelLeft,
  PanelRight,
  SearchX,
  X,
} from "lucide-react";
import {
  api,
  candidateToSpec,
  type ScannedProject,
  type ServiceCandidate,
  type SvcState,
} from "../../lib/api";
import { useApp } from "../../lib/ctx";
import { useT } from "../../lib/i18n";
import { setUiSetting } from "../../lib/settings";
import { markPending, useDash } from "../../lib/store";
import { cn } from "../../lib/utils";
import { StatusDot, ThemePicker } from "../bits";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogTitle } from "../ui/dialog";

const STEPS = ["THEME", "PROJECT_FOLDERS", "LAUNCH", "DONE"] as const;

const STATE_LABEL: Record<SvcState, string> = {
  up: "STATE_RUNNING",
  dead: "STATE_CRASHED",
  failed: "STATE_CRASHED",
  off: "STATE_STOPPED",
  down: "STATE_DOWN",
  check: "STATE_CHECKING",
};

/** First run: 4-step setup wizard (choices, not questions —
   everything is preselected, "Next" sails through). */
export function OnboardingDialog() {
  const app = useApp();
  const t = useT();
  const dash = useDash();
  const [step, setStep] = useState(0);
  const [roots, setRoots] = useState<string[] | null>(null);
  const [autoRoots, setAutoRoots] = useState<string[]>([]);
  const [found, setFound] = useState<ScannedProject[] | null>(null);
  const [scanning, setScanning] = useState(false);
  const [launched, setLaunched] = useState<Set<string>>(new Set());
  const [cands, setCands] = useState<ServiceCandidate[] | null>(null);

  useEffect(() => {
    api.settings().then((s) => {
      setRoots(s.scan_roots);
      setAutoRoots(s.scan_roots_auto ?? []);
    });
  }, []);

  const rescan = () => {
    setScanning(true);
    api
      .scan()
      .then((r) => setFound(r.found))
      .catch(() => {})
      .finally(() => setScanning(false));
  };
  // the "N projects" count is fresh when entering the folders step and the final
  useEffect(() => {
    if (step >= 1) rescan();
  }, [step]);

  // fallback for the launch step: a process scan (~1s) — fetch once, only
  // when the folder scan found nothing to run
  useEffect(() => {
    if (step === 2 && found !== null && found.length === 0 && cands === null)
      api
        .serviceCandidates()
        .then(setCands)
        .catch(() => setCands([]));
  }, [step, found, cands]);

  const launch = async (p: ScannedProject) => {
    setLaunched((s) => new Set(s).add(p.name));
    markPending(p.name, "up");
    await api.addProjects([p]).catch(() => {});
    api.prjAction(p.name, "start").catch(() => {});
  };
  const launchCand = async (c: ServiceCandidate) => {
    setLaunched((s) => new Set(s).add(c.name));
    markPending(c.name, "up");
    await api.saveService("", candidateToSpec(c)).catch(() => {});
    api.svcAction(c.name, "start").catch(() => {});
  };

  const liveOf = (name: string) =>
    dash?.projects.find((x) => x.name === name)?.state ??
    dash?.services.find((x) => x.name === name)?.state ??
    dash?.remotes.find((x) => x.name === name)?.state;

  // launch rows: scanned projects first, detected service candidates when empty
  const launchItems = found?.length
    ? found
        .slice(0, 3)
        .map((p) => ({ name: p.name, cmd: p.cmd, start: () => launch(p) }))
    : (cands ?? [])
        .filter((c) => c.start)
        .sort(
          (a, b) =>
            Number(b.why?.includes("WHY_AUTORUN") ?? false) -
              Number(a.why?.includes("WHY_AUTORUN") ?? false) ||
            b.score - a.score,
        )
        .slice(0, 2)
        .map((c) => ({
          name: c.name,
          cmd: c.start,
          start: () => launchCand(c),
        }));

  const saveRoots = (next: string[]) => {
    setRoots(next);
    api.saveSettings({ scan_roots: next }).then(() => rescan());
  };
  const addRoot = () =>
    api.pickDir(roots?.[roots.length - 1] || "").then((r) => {
      if (r.dir && !roots?.includes(r.dir))
        saveRoots([...(roots ?? []), r.dir]);
    });

  const countFor = (root: string) => {
    // +sep: root C:\apps must not count projects from C:\apps2
    const r = root.replaceAll("/", "\\").replace(/\\+$/, "").toLowerCase() + "\\";
    return (
      found?.filter((p) =>
        (p.cwd.replaceAll("/", "\\") + "\\").toLowerCase().startsWith(r),
      ).length ?? 0
    );
  };

  // Esc/backdrop just marks done — only the finish CTA navigates
  const done = () => {
    setUiSetting("onboarded", true);
    app.closeDlg();
  };
  const finish = () => {
    done();
    // strip on the projects tab shows the same scan results
    if (found?.length) app.setSection("projects");
  };

  return (
    <Dialog open onOpenChange={(v) => !v && done()}>
      <DialogContent className="max-w-xl gap-0 p-0">
        <DialogTitle className="sr-only">{t("INITIAL_SETUP")}</DialogTitle>

        {/* progress: steps + dots — always visible how much is left */}
        <div className="flex items-center justify-between border-b border-(--border-hairline) px-5 py-3.5">
          <span className="text-[13px] font-medium text-(--text-primary)">
            {t("SETUP_TITLE")}
          </span>
          <div className="flex items-center gap-1.5">
            {STEPS.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 w-1.5 rounded-full transition-colors",
                  i === step
                    ? "bg-(--accent)"
                    : i < step
                      ? "bg-(--accent)/60"
                      : "bg-(--border-strong)",
                )}
              />
            ))}
            <span className="ml-1.5 text-[11px] text-(--text-muted)">
              {step + 1} / {STEPS.length}
            </span>
          </div>
        </div>

        <div className="min-h-[340px] px-5 py-4">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 18 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -18 }}
              transition={{ duration: 0.16, ease: "easeOut" }}
            >
              {step === 0 && (
                <>
                  <h2 className="text-[15px] font-semibold text-(--text-primary)">
                    {t("APPEARANCE")}
                  </h2>
                  <p className="mt-1 text-[12.5px] text-(--text-muted)">
                    {t("PICK_THEME_HINT")}
                  </p>
                  <ThemePicker className="mt-3" />
                </>
              )}

              {step === 1 && (
                <>
                  <h2 className="text-[15px] font-semibold text-(--text-primary)">
                    {t("PROJECT_FOLDERS")}
                  </h2>
                  <p className="mt-1 text-[12.5px] text-(--text-muted)">
                    {t("DASHBOARD_SEARCHES")} <code>package.json</code>{" "}
                    {t("SEARCH_FOLDERS_HINT")}
                  </p>
                  <div className="mt-3 space-y-1.5">
                    {roots === null ? (
                      <div className="flex items-center gap-2 py-4 text-[12px] text-(--text-muted)">
                        <Loader2 size={14} className="animate-spin" /> {t("LOADING")}
                      </div>
                    ) : (
                      <>
                        {roots.length === 0 && autoRoots.length > 0 && (
                          <div className="rounded-md border border-(--border-hairline) bg-(--bg-surface)/20 px-3 py-2 font-mono text-[11.5px] text-(--text-muted)">
                            {t("SCAN_ROOTS_AUTO", {
                              dirs: autoRoots.join(", "),
                            })}
                          </div>
                        )}
                        {roots.map((r) => (
                        <div
                          key={r}
                          className="flex items-center gap-2.5 rounded-md border border-(--border-hairline) bg-(--bg-surface)/40 px-3 py-2"
                        >
                          <FolderOpen
                            size={15}
                            strokeWidth={1.75}
                            className="shrink-0 text-(--accent)"
                          />
                          <span
                            className="min-w-0 flex-1 truncate font-mono text-[11.5px] text-(--text-secondary)"
                            title={r}
                          >
                            {r}
                          </span>
                          <span className="tnum shrink-0 text-[10.5px] text-(--text-muted)">
                            {scanning && !found
                              ? "…"
                              : countFor(r) > 0
                                ? t("N_PROJECTS", { n: countFor(r) })
                                : t("EMPTY")}
                          </span>
                          <button
                            onClick={() =>
                              saveRoots(roots.filter((x) => x !== r))
                            }
                            aria-label={t("REMOVE_FOLDER")}
                            className="shrink-0 cursor-pointer rounded p-0.5 text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--status-red)"
                          >
                            <X size={13} strokeWidth={2} />
                          </button>
                        </div>
                      ))}
                      </>
                    )}
                    <button
                      onClick={addRoot}
                      className="flex w-full cursor-pointer items-center justify-center gap-1.5 rounded-md border border-dashed border-(--border-strong) px-3 py-2 text-[12px] text-(--text-secondary) transition-colors hover:border-(--accent) hover:text-(--accent-text)"
                    >
                      <FolderPlus size={14} strokeWidth={1.75} /> {t("ADD_FOLDER")}
                    </button>
                  </div>
                </>
              )}

              {step === 2 && (
                <>
                  <h2 className="text-[15px] font-semibold text-(--text-primary)">
                    {t("LAUNCH_FIRST_SERVICE")}
                  </h2>
                  <p className="mt-1 text-[12.5px] text-(--text-muted)">
                    {t("LAUNCH_FIRST_HINT")}
                  </p>
                  <div className="mt-3 space-y-1.5">
                    {found === null || (!found.length && cands === null) ? (
                      <div className="flex items-center gap-2 py-4 text-[12px] text-(--text-muted)">
                        <Loader2 size={14} className="animate-spin" />{" "}
                        {t("LOADING")}
                      </div>
                    ) : launchItems.length === 0 ? (
                      <div className="flex items-center gap-2.5 rounded-md border border-dashed border-(--border-strong) px-3 py-4 text-[12px] text-(--text-muted)">
                        <SearchX size={15} strokeWidth={1.5} className="shrink-0" />
                        {t("NOTHING_TO_LAUNCH")}
                      </div>
                    ) : (
                      launchItems.map((it) => {
                        const on = launched.has(it.name);
                        const live = liveOf(it.name);
                        return (
                          <div
                            key={it.name}
                            className="flex items-center gap-2.5 rounded-md border border-(--border-hairline) bg-(--bg-surface)/40 px-3 py-2"
                          >
                            {/* off dot pre-launch keeps the 8px slot stable — no shift on start */}
                            <StatusDot state={live ?? (on ? "check" : "off")} />
                            <div className="min-w-0 flex-1">
                              <div className="truncate text-[12.5px] font-medium text-(--text-primary)">
                                {it.name}
                              </div>
                              <div
                                className="truncate font-mono text-[11px] text-(--text-muted)"
                                title={it.cmd}
                              >
                                {it.cmd}
                              </div>
                            </div>
                            {on ? (
                              <span className="shrink-0 text-[11.5px] text-(--text-muted)">
                                {live ? t(STATE_LABEL[live] ?? live) : t("STATE_CHECKING")}
                              </span>
                            ) : (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={it.start}
                              >
                                {t("ADD_AND_RUN")}
                              </Button>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </>
              )}

              {step === 3 && (
                <>
                  <h2 className="text-[15px] font-semibold text-(--text-primary)">
                    {t("ALL_DONE")}
                  </h2>
                  <p className="mt-1 text-[12.5px] text-(--text-muted)">
                    {found === null
                      ? t("SCANNING_FOLDERS")
                      : found.length
                        ? t("FOUND_PROJECTS_HINT", { n: found.length })
                        : t("HOTKEYS_LEFT")}
                  </p>
                  {launched.size > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40 px-3 py-2.5">
                      <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-(--text-muted)">
                        {t("SETUP_RUNNING_NOW")}
                      </span>
                      {[...launched].map((n) => (
                        <span
                          key={n}
                          className="inline-flex items-center gap-1.5 text-[12px] text-(--text-secondary)"
                        >
                          <StatusDot state={liveOf(n) ?? "check"} />
                          {n}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="mt-3 space-y-2 rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40 p-3 text-[12.5px] text-(--text-secondary)">
                    <div className="flex items-center gap-2.5">
                      <Command
                        size={15}
                        strokeWidth={1.75}
                        className="shrink-0 text-(--accent)"
                      />
                      <span>
                        <kbd className="kbd">Ctrl+K</kbd> — {t("SEARCH_SERVICES_ACTIONS")}
                      </span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <PanelLeft
                        size={15}
                        strokeWidth={1.75}
                        className="shrink-0 text-(--accent)"
                      />
                      <span>
                        {t("SIDEBAR_EDGE_HINT")}
                      </span>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <PanelRight
                        size={15}
                        strokeWidth={1.75}
                        className="shrink-0 text-(--accent)"
                      />
                      <span>
                        <kbd className="kbd">Ctrl+I</kbd> — {t("INSPECTOR_DESC")}
                      </span>
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* wizard footer: skip on the left, navigation on the right */}
        <div className="flex items-center justify-between border-t border-(--border-hairline) px-5 py-3">
          <button
            onClick={done}
            className="cursor-pointer text-[12px] text-(--text-muted) transition-colors hover:text-(--text-secondary)"
          >
            {t("SKIP")}
          </button>
          <div className="flex items-center gap-2">
            {step > 0 && (
              <Button variant="ghost" size="sm" onClick={() => setStep(step - 1)}>
                <ChevronLeft size={14} strokeWidth={1.75} /> {t("BACK")}
              </Button>
            )}
            {step < STEPS.length - 1 ? (
              <Button size="sm" onClick={() => setStep(step + 1)}>
                {t("NEXT")} <ChevronRight size={14} strokeWidth={1.75} />
              </Button>
            ) : (
              <Button size="sm" onClick={finish}>
                {found?.length
                  ? t("START_ADD_PROJECTS", { n: found.length })
                  : t("DONE")}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
