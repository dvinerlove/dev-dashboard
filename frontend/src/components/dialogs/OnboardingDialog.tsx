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
  X,
} from "lucide-react";
import { api, type ScannedProject } from "../../lib/api";
import { useApp } from "../../lib/ctx";
import { useT } from "../../lib/i18n";
import { setUiSetting } from "../../lib/settings";
import { cn } from "../../lib/utils";
import { ThemePicker } from "../bits";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogTitle } from "../ui/dialog";

const STEPS = ["THEME", "PROJECT_FOLDERS", "DONE"] as const;

/** Первый запуск: мастер настройки в 3 шага (choices, not questions —
   всё предвыбрано, «Далее» проходит насквозь). */
export function OnboardingDialog() {
  const app = useApp();
  const t = useT();
  const [step, setStep] = useState(0);
  const [roots, setRoots] = useState<string[] | null>(null);
  const [found, setFound] = useState<ScannedProject[] | null>(null);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    api.settings().then((s) => setRoots(s.scan_roots));
  }, []);

  const rescan = () => {
    setScanning(true);
    api
      .scan()
      .then((r) => setFound(r.found))
      .finally(() => setScanning(false));
  };
  // счёт «N проектов» свежий при входе на шаг папок и в финал
  useEffect(() => {
    if (step >= 1) rescan();
  }, [step]);

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
    // +sep: root C:\apps не должен считать проекты из C:\apps2
    const r = root.replaceAll("/", "\\").replace(/\\+$/, "").toLowerCase() + "\\";
    return (
      found?.filter((p) =>
        (p.cwd.replaceAll("/", "\\") + "\\").toLowerCase().startsWith(r),
      ).length ?? 0
    );
  };

  const done = () => {
    setUiSetting("onboarded", true);
    app.closeDlg();
    if (found?.length) app.openDlg({ t: "scan", items: found });
  };

  return (
    <Dialog open onOpenChange={(v) => !v && done()}>
      <DialogContent className="max-w-xl gap-0 p-0">
        <DialogTitle className="sr-only">{t("INITIAL_SETUP")}</DialogTitle>

        {/* прогресс: шаги + точки — всегда видно, сколько осталось */}
        <div className="flex items-center justify-between border-b border-(--border-hairline) px-5 py-3.5">
          <span className="text-[13px] font-medium text-(--text-primary)">
            {t("SETUP_TITLE")}
          </span>
          <div className="flex items-center gap-1.5">
            {STEPS.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 rounded-full transition-[width,background-color] duration-300",
                  i === step
                    ? "w-5 bg-(--accent)"
                    : i < step
                      ? "w-1.5 bg-(--accent)/60"
                      : "w-1.5 bg-(--border-strong)",
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
                    {t("DASHBOARD_SEARCHES")} <code className="kbd">package.json</code>{" "}
                    {t("SEARCH_FOLDERS_HINT")}
                  </p>
                  <div className="mt-3 space-y-1.5">
                    {roots === null ? (
                      <div className="flex items-center gap-2 py-4 text-[12px] text-(--text-muted)">
                        <Loader2 size={14} className="animate-spin" /> {t("LOADING")}
                      </div>
                    ) : (
                      roots.map((r) => (
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
                          <span
                            className={cn(
                              "tnum shrink-0 rounded px-1.5 py-0.5 text-[10.5px]",
                              countFor(r) > 0
                                ? "bg-(--status-green)/15 text-(--status-green)"
                                : "text-(--text-muted)",
                            )}
                          >
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
                      ))
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
                    {t("ALL_DONE")}
                  </h2>
                  <p className="mt-1 text-[12.5px] text-(--text-muted)">
                    {found === null
                      ? t("SCANNING_FOLDERS")
                      : found.length
                        ? t("FOUND_PROJECTS_HINT", { n: found.length })
                        : t("HOTKEYS_LEFT")}
                  </p>
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

        {/* футер визарда: пропуск слева, навигация справа */}
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
              <Button size="sm" onClick={done}>
                {found?.length
                  ? t("START_ADD_PROJECTS", { n: found.length })
                  : t("GET_STARTED")}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
