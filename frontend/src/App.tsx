import { useEffect, useMemo, useRef, useState } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { toast, Toaster } from "sonner";
import { api } from "./lib/api";
import {
  AppCtx,
  SECTION_TITLES,
  type AppApi,
  type Dlg,
  type Section,
  type Sel,
} from "./lib/ctx";
import { getDash, markPending, refresh, useDash } from "./lib/store";
import { applyTheme, initTheme, type ThemeId } from "./lib/theme";
import { setLang, t, useLang } from "./lib/i18n";
import { setUiSetting, uiSetting } from "./lib/settings";
import { AutorunView } from "./components/AutorunView";
import { CommandPalette } from "./components/CommandPalette";
import { EventsView } from "./components/EventsView";
import { Inspector } from "./components/Inspector";
import { OverviewView } from "./components/OverviewView";
import { PortsView } from "./components/PortsView";
import { ProjectsGrid } from "./components/ProjectCards";
import { ServiceList } from "./components/ServiceRows";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { SectionTitle, SkeletonRows } from "./components/bits";
import { Button } from "./components/ui/button";
import { TooltipProvider } from "./components/ui/tooltip";
import {
  AutorunDialog,
  ConfirmDialog,
  KillPortDialog,
  PortConflictDialog,
  ScanDialog,
  TokenDialog,
} from "./components/dialogs/SimpleDialogs";
import { OnboardingDialog } from "./components/dialogs/OnboardingDialog";
import { ProjectDialog } from "./components/dialogs/ProjectDialog";
import { ServiceDialog } from "./components/dialogs/ServiceDialog";
import { SettingsView } from "./components/SettingsView";

export default function App() {
  const st = useDash();
  const [theme, setThemeState] = useState<ThemeId>(initTheme);
  const setTheme = (t: ThemeId) => {
    applyTheme(t);
    setThemeState(t);
  };
  const [section, setSection] = useState<Section>("overview");
  const [sel, setSel] = useState<Sel | null>(null);
  const [inspector, setInspectorState] = useState(() =>
    uiSetting("inspectorOpen", true),
  );
  const setInspector = (v: boolean) => {
    setInspectorState(v);
    setUiSetting("inspectorOpen", v);
  };
  const [inspectorTab, setInspectorTab] = useState("logs");
  const [palette, setPalette] = useState(false);
  const [dlg, setDlg] = useState<Dlg>(null);
  const autoSelected = useRef(false);

  // сайдбар: авто-rail на узком окне + ручной оверрайд, который живёт до
  // следующего пересечения порога (паттерн VS Code/shadcn)
  const RAIL_AUTO = 1150;
  const [railNarrow, setRailNarrow] = useState(
    () => window.innerWidth < RAIL_AUTO,
  );
  const [railOverride, setRailOverride] = useState<boolean | null>(null);
  const [railAuto, setRailAutoState] = useState(() =>
    uiSetting("railAuto", true),
  );
  const setRailAuto = (v: boolean) => {
    setRailAutoState(v);
    setUiSetting("railAuto", v);
  };
  useEffect(() => {
    const mq = matchMedia(`(max-width:${RAIL_AUTO}px)`);
    const f = () => setRailNarrow(mq.matches);
    mq.addEventListener("change", f);
    return () => mq.removeEventListener("change", f);
  }, []);
  useEffect(() => setRailOverride(null), [railNarrow]);
  const rail =
    theme === "console" || (railOverride ?? (railAuto && railNarrow));

  // paper-инспектор: док пока главной колонке хватает места —
  // winW − sidebar − inspector ≥ minMain текущей страницы; иначе —
  // плавающий «лист». minMain — минимальная полезная ширина контента
  // (как aux panel у VS Code/Notion: док живёт до fit-границы контента).
  const INSP_W = { min: 300, def: 380, max: 560 };
  const MIN_MAIN: Partial<Record<Section, number>> = {
    overview: 620,
    infra: 560,
    projects: 600,
    ports: 560,
    autorun: 540,
    events: 480,
    settings: 520,
  };
  const [winW, setWinW] = useState(() => window.innerWidth);
  const [inspW, setInspW] = useState(() => uiSetting("inspW", INSP_W.def));
  const [inspDrag, setInspDrag] = useState(false);
  useEffect(() => {
    const f = () => setWinW(window.innerWidth);
    window.addEventListener("resize", f);
    return () => window.removeEventListener("resize", f);
  }, []);
  const sidebarW = rail ? 48 : 196;
  const inspDock =
    winW - sidebarW - inspW >= (MIN_MAIN[section] ?? 560);

  // ручка ресайза дока (как PanelResizeHandle у graphite/console):
  // ширина живо следует за курсором, клэмп не даёт вытеснить контент —
  // дальше maxW док сам уйдёт в оверлей при сужении окна
  const inspDragStart = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    e.preventDefault();
    const el = e.currentTarget;
    const x0 = e.clientX;
    let w = inspW;
    el.setPointerCapture(e.pointerId);
    setInspDrag(true);
    document.body.style.cursor = "ew-resize";
    document.body.style.userSelect = "none";
    const move = (ev: PointerEvent) => {
      const maxW = Math.max(
        INSP_W.min,
        Math.min(INSP_W.max, winW - sidebarW - (MIN_MAIN[section] ?? 560)),
      );
      w = Math.max(INSP_W.min, Math.min(maxW, inspW + x0 - ev.clientX));
      setInspW(w);
    };
    el.addEventListener("pointermove", move);
    el.addEventListener(
      "pointerup",
      () => {
        el.removeEventListener("pointermove", move);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        setInspDrag(false);
        setUiSetting("inspW", w);
      },
      { once: true },
    );
  };

  const lang = useLang();
  // язык бэкенда (settings.json) — источник истины; state-полл тащит его
  useEffect(() => {
    if (st?.lang === "ru" || st?.lang === "en") {
      setLang(st.lang);
      document.documentElement.lang = st.lang;
    }
  }, [st?.lang]);

  useEffect(() => {
    document.title = `${t(SECTION_TITLES[section])} — Dev Dashboard`;
  }, [section, lang]);

  // первый сервис выбирается автоматически при первой загрузке
  useEffect(() => {
    if (!autoSelected.current && st?.services.length) {
      autoSelected.current = true;
      setSel({ kind: "svc", name: st.services[0].name });
    }
  }, [st]);

  // первый запуск с пустой конфигурацией — мастер настройки (один раз,
  // флаг onboarded + ref держат против повторного открытия на поллах)
  const onboardedShown = useRef(false);
  useEffect(() => {
    if (
      !st ||
      dlg ||
      onboardedShown.current ||
      uiSetting("onboarded", false) ||
      st.services.length > 0 ||
      st.projects.length > 0
    )
      return;
    onboardedShown.current = true;
    setDlg({ t: "onboarding" });
  }, [st, dlg]);

  const app = useMemo<AppApi>(() => {
    // state читаем лениво через getDash() — иначе каждый 2с-полл
    // менял бы identity app и ре-рендерил всё дерево контекста
    const findSvc = (name: string, remote?: boolean) => {
      const s = getDash();
      return [...(s?.services ?? []), ...(s?.remotes ?? [])].find(
        (r) => r.name === name && (remote === undefined || !!r.remote === !!remote),
      );
    };
    const confirm = (
      title: string,
      body: string,
      action: string,
      run: () => void,
      danger?: boolean,
    ) => setDlg({ t: "confirm", title, body, action, danger, run });

    return {
      theme, setTheme,
      section, setSection, sel, select: setSel,
      inspector, setInspector, inspectorTab, setInspectorTab,
      palette, setPalette,
      railAuto, setRailAuto,
      openDlg: setDlg, closeDlg: () => setDlg(null),
      toast: (m) => toast(m),

      async svcToggle(name, remote) {
        const row = findSvc(name, remote);
        const stopNow = () => {
          markPending(name, "down");
          api.svcAction(name, "stop");
        };
        const startNow = () => {
          markPending(name, "up");
          api.svcAction(name, "start");
        };
        if (row?.state === "up") {
          const tg = await api.serviceTargets(name);
          if (!tg.length) return void stopNow();
          confirm(
            t("STOP_NAME_CONFIRM", { n: name }),
            t("WILL_TERMINATE") + "\n" +
              tg.map((x) => `${x.name} (pid ${x.pid})`).join("\n"),
            t("STOP"),
            stopNow,
            true,
          );
        } else {
          const c = await api.portConflict(name);
          if (c.pid && c.port && c.pname)
            setDlg({
              t: "portconflict",
              name,
              c: { port: c.port, pid: c.pid, pname: c.pname,
                   suggest: c.suggest },
            });
          else startNow();
        }
      },
      async svcRestart(name) {
        const go = () => {
          markPending(name, "up");
          api.svcAction(name, "restart");
        };
        const tg = await api.serviceTargets(name);
        if (!tg.length) return void go();
        confirm(
          t("RESTART_NAME_CONFIRM", { n: name }),
          t("WILL_TERMINATE") + "\n" +
            tg.map((x) => `${x.name} (pid ${x.pid})`).join("\n"),
          t("RESTART"),
          go,
        );
      },
      prjToggle(name) {
        const p = getDash()?.projects.find((x) => x.name === name);
        markPending(name, p?.running ? "down" : "up");
        api.prjAction(name, p?.running ? "stop" : "start");
      },
      chip(kind, name) {
        const row =
          kind === "prj"
            ? getDash()?.projects.find((x) => x.name === name)
            : findSvc(name, kind === "remote" ? true : kind === "svc" ? false : undefined);
        if (row?.chipUrl && row.chipUrl !== "copy") api.openUrl(row.chipUrl);
        else if (row?.chip) {
          navigator.clipboard
            .writeText(String(row.chip).replace(/^:/, ""))
            .catch(() => {});
          toast(t("COPIED_VALUE", { v: row.chip }));
        }
      },
      startAll() {
        api.startAll();
        toast(t("STARTING_ALL"));
      },
      async stopAll() {
        const names = await api.stopAllTargets();
        if (!names.length) return;
        confirm(
          t("STOP_ALL_CONFIRM"),
          names.join(", "),
          t("STOP"),
          () => api.stopAll(),
          true,
        );
      },
      scan() {
        const tid = toast.loading(t("SCANNING"));
        api
          .scan()
          .then((r) => {
            toast.dismiss(tid);
            if (!r.found.length) toast(t("NO_NEW_PROJECTS"));
            else setDlg({ t: "scan", items: r.found });
          })
          .catch(() => {
            toast.dismiss(tid);
            toast(t("SCAN_FAILED"));
          });
      },
      async killPortFlow(port) {
        const tg = await api.portTargets(port);
        const run = () =>
          api.killPort(port).then((r) => {
            toast(r.msg || t("DONE"));
            refresh();
          });
        if (tg.length)
          confirm(
            t("FREE_PORT_CONFIRM", { p: port }),
            t("WILL_TERMINATE") + "\n" +
              tg.map((x) => `${x.name} (pid ${x.pid})`).join("\n"),
            t("KILL"),
            run,
            true,
          );
        else run();
      },
      deleteService(name) {
        confirm(
          t("DELETE_NAME_CONFIRM", { n: name }),
          t("SERVICE_DELETE_BODY"),
          t("DELETE"),
          () => api.deleteService(name).then(() => refresh()),
          true,
        );
      },
      deleteProject(name, running) {
        if (running) return toast(t("STOP_BEFORE_DELETE"));
        confirm(
          t("DELETE_NAME_CONFIRM", { n: name }),
          t("PROJECT_DELETE_BODY"),
          t("DELETE"),
          () => api.deleteProject(name).then(() => refresh()),
          true,
        );
      },
      editService(name) {
        api.serviceSpec(name).then((s) => setDlg({ t: "service", spec: s }));
      },
      editProject(name) {
        const p = getDash()?.projects.find((x) => x.name === name);
        if (p?.running) return toast(t("STOP_BEFORE_EDIT"));
        api.projectSpec(name).then((s) => setDlg({ t: "project", spec: s }));
      },
      editAutorun(name, cmd, mine) {
        const open = () => setDlg({ t: "autorun", name, cmd });
        if (mine === false)
          confirm(
            t("EDIT_NAME_CONFIRM", { n: name }),
            t("AUTORUN_FOREIGN_HINT"),
            t("EDIT_ENTRY"),
            open,
          );
        else open();
      },
      deleteAutorun(name) {
        confirm(
          t("REMOVE_AUTORUN_CONFIRM", { n: name }),
          t("AUTORUN_DELETE_BODY"),
          t("REMOVE"),
          () => api.autorunDelete(name).then(() => refresh()),
          true,
        );
      },
      showRuns(name, kind) {
        setSel({ kind, name });
        setInspector(true);
        setInspectorTab("runs");
      },
      confirm,
    };
  }, [section, sel, inspector, inspectorTab, palette, theme, railAuto]);

  // навигация стрелками по списку
  useEffect(() => {
    const nav = (dir: 1 | -1) => {
      const s = getDash();
      if (!s) return;
      const list: Sel[] =
        section === "projects"
          ? s.projects.map((p) => ({ kind: "prj" as const, name: p.name }))
          : [
              ...s.services.map((s) => ({ kind: "svc" as const, name: s.name })),
              ...s.remotes.map((s) => ({
                kind: "svc" as const,
                name: s.name,
                remote: true,
              })),
            ];
      if (!list.length) return;
      const i = list.findIndex((x) => x.name === sel?.name && x.kind === sel.kind);
      const next = list[(i + dir + list.length) % list.length];
      setSel(next);
    };
    const h = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      const tag = el?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA";
      // стрелки не трогаем, если фокус внутри меню/палитры/диалога — Radix сам
      const inOverlay =
        e.defaultPrevented ||
        !!el?.closest?.('[role="menu"],[role="listbox"],[role="dialog"],[cmdk-root]');
      if (e.ctrlKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette((v) => !v);
      } else if (e.ctrlKey && e.key.toLowerCase() === "i") {
        e.preventDefault();
        setInspector(!inspector);
      } else if (!typing && !inOverlay && (e.key === "ArrowDown" || e.key === "ArrowUp") && !dlg && !palette) {
        e.preventDefault();
        nav(e.key === "ArrowDown" ? 1 : -1);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [section, sel, dlg, palette, inspector]);

  return (
    <AppCtx.Provider value={app}>
      <TooltipProvider delayDuration={350}>
        {/* inert глушит фокус/клики под палитрой — дешёвый аналог aria-modal */}
        <div className="flex h-full flex-col bg-(--bg-base)" inert={palette}>
          <Topbar />
          <div
            className={`relative flex min-h-0 flex-1 ${inspDrag ? "" : "transition-[padding-right] duration-300 ease-(--ease-out)"}`}
            style={{
              paddingRight:
                inspector && theme.startsWith("paper") && inspDock ? inspW : 0,
            }}
          >
            <Sidebar
              rail={rail}
              canToggle={theme !== "console"}
              onToggle={() => setRailOverride(!rail)}
            />
            <PanelGroup
              direction={theme === "console" ? "vertical" : "horizontal"}
              className="min-w-0 flex-1"
            >
              <Panel id="main" order={1} minSize={30} className="min-w-0">
                <main className="h-full overflow-y-auto bg-(--bg-canvas) p-5">
                  {section === "overview" && <OverviewView />}
                  {section === "infra" && (
                    <>
                      <SectionTitle
                        right={
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => app.openDlg({ t: "service", spec: null })}
                          >
                            {t("ADD_SERVICE")}
                          </Button>
                        }
                      >
                        {t("INFRASTRUCTURE")}
                      </SectionTitle>
                      {st ? (
                        <ServiceList rows={st.services} />
                      ) : (
                        <SkeletonRows n={7} />
                      )}
                      {!!st?.remotes.length && (
                        <>
                          <SectionTitle className="mt-4">
                            {t("INFRA_REMOTE")}
                          </SectionTitle>
                          <ServiceList rows={st.remotes} />
                        </>
                      )}
                    </>
                  )}
                  {section === "projects" && (
                    <>
                      <SectionTitle
                        right={
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => app.openDlg({ t: "project", spec: null })}
                          >
                            {t("ADD_PROJECT")}
                          </Button>
                        }
                      >
                        {t("SECTION_PROJECTS")}
                      </SectionTitle>
                      {st ? (
                        <ProjectsGrid rows={st.projects} />
                      ) : (
                        <SkeletonRows n={3} />
                      )}
                    </>
                  )}
                  {section === "autorun" && (
                    <AutorunView
                      mine={st?.autorunMine ?? []}
                      other={st?.autorunOther ?? []}
                    />
                  )}
                  {section === "events" && <EventsView />}
                  {section === "ports" && <PortsView />}
                  {section === "settings" && <SettingsView />}
                </main>
              </Panel>
              {inspector && theme === "console" && (
                <>
                  <PanelResizeHandle className="h-px bg-(--border-hairline) transition-colors hover:bg-(--accent) data-[resize-handle-state=drag]:bg-(--accent)" />
                  <Panel
                    id="inspector"
                    order={2}
                    defaultSize={38}
                    minSize={18}
                    maxSize={70}
                  >
                    <Inspector />
                  </Panel>
                </>
              )}
              {inspector && theme === "graphite" && (
                <>
                  <PanelResizeHandle className="w-px bg-(--border-hairline) transition-colors hover:bg-(--accent) data-[resize-handle-state=drag]:bg-(--accent)" />
                  <Panel
                    id="inspector"
                    order={2}
                    defaultSize={32}
                    minSize={22}
                    maxSize={45}
                    className="min-w-0 max-w-[480px] overflow-hidden"
                  >
                    <Inspector />
                  </Panel>
                </>
              )}
            </PanelGroup>
            {/* paper: на узком окне инспектор — плавающий «лист» поверх
                контента, на широком — док; морф анимируется инсетами,
                радиусом и тенью, элемент не перемонтируется */}
            {inspector && theme.startsWith("paper") && (
              <div
                className={`absolute z-30 overflow-hidden bg-(--bg-surface) ${inspDrag ? "" : "transition-[top,right,bottom,border-width,border-color,border-radius,box-shadow] duration-300 ease-(--ease-out)"} ${
                  inspDock
                    ? "top-0 right-0 bottom-0 rounded-none border-l border-(--border-hairline)"
                    : "top-3 right-3 bottom-3 rounded-xl border border-(--border-strong) shadow-[-18px_0_44px_-14px_rgba(40,38,60,0.3)]"
                }`}
                style={{ width: inspW }}
              >
                {inspDock && (
                  <div
                    className="absolute inset-y-0 left-0 z-40 w-1 cursor-ew-resize transition-colors hover:bg-(--accent) active:bg-(--accent)"
                    onPointerDown={inspDragStart}
                  />
                )}
                <Inspector />
              </div>
            )}
          </div>
        </div>

        <CommandPalette />
        {dlg?.t === "confirm" && <ConfirmDialog d={dlg} />}
        {dlg?.t === "portconflict" && <PortConflictDialog d={dlg} />}
        {dlg?.t === "killport" && <KillPortDialog />}
        {dlg?.t === "autorun" && <AutorunDialog d={dlg} />}
        {dlg?.t === "token" && <TokenDialog d={dlg} />}
        {dlg?.t === "scan" && <ScanDialog d={dlg} />}
        {dlg?.t === "service" && <ServiceDialog spec={dlg.spec} />}
        {dlg?.t === "project" && <ProjectDialog spec={dlg.spec} />}
        {dlg?.t === "onboarding" && <OnboardingDialog />}

        <Toaster
          theme={theme === "paper" ? "light" : "dark"}
          position="bottom-right"
          toastOptions={{
            style: {
              background: "var(--bg-surface)",
              border: "1px solid var(--border-strong)",
              color: "var(--text-primary)",
              fontSize: "12px",
            },
          }}
        />
      </TooltipProvider>
    </AppCtx.Provider>
  );
}
