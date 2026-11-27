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
import { startupUpdateCheck } from "./lib/update";
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
import { ProjectsStrip } from "./components/ProjectsStrip";
import { ServiceList } from "./components/ServiceRows";
import { CandidatesStrip } from "./components/CandidatesStrip";
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

  // sidebar: auto-rail on narrow windows + manual override that lives until
  // the next threshold crossing (VS Code/shadcn pattern)
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

  // paper inspector: docked while the main column has room —
  // winW − sidebar − inspector ≥ minMain of the current page; otherwise —
  // a floating "sheet". minMain is the minimum usable content width
  // (like the aux panel in VS Code/Notion: dock lives until the content fit boundary).
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

  // dock resize handle (like PanelResizeHandle in graphite/console):
  // width follows the cursor live, the clamp keeps it from pushing content out —
  // past maxW the dock itself goes overlay as the window shrinks
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
  // backend language (settings.json) is the source of truth; the state poll carries it
  useEffect(() => {
    if (st?.lang === "ru" || st?.lang === "en") {
      setLang(st.lang);
      document.documentElement.lang = st.lang;
    }
  }, [st?.lang]);

  useEffect(() => {
    document.title = `${t(SECTION_TITLES[section])} — Dev Dashboard`;
  }, [section, lang]);

  // passive update check — one background fetch per session, silent
  useEffect(() => {
    if (st?.version) startupUpdateCheck(st.version);
  }, [st?.version]);

  // the first service is auto-selected on first load
  useEffect(() => {
    if (!autoSelected.current && st?.services.length) {
      autoSelected.current = true;
      setSel({ kind: "svc", name: st.services[0].name });
    }
  }, [st]);

  // first run with an empty config — setup wizard (once,
  // the onboarded flag + ref guard against reopening on polls)
  const onboardedShown = useRef(false);
  useEffect(() => {
    if (
      !st ||
      dlg ||
      onboardedShown.current ||
      uiSetting("onboarded", false) ||
      st.services.length > 0 ||
      st.projects.length > 0 ||
      st.remotes.length > 0
    )
      return;
    onboardedShown.current = true;
    setDlg({ t: "onboarding" });
  }, [st, dlg]);

  const app = useMemo<AppApi>(() => {
    // state is read lazily via getDash() — otherwise every 2s poll
    // would change the app identity and re-render the whole context tree
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
      // click on any row with inspector content: select + open.
      // (auto-select on load stays `select` — must not reopen a
      // panel the user deliberately closed)
      openItem: (s) => {
        setSel(s);
        setInspector(true);
      },
      // owner strings (ports view) carry no kind — resolve by name
      openNamed: (name) => {
        const s = findSvc(name);
        if (s) {
          setSel({ kind: "svc", name: s.name, remote: s.remote });
          setInspector(true);
        } else if (getDash()?.projects.some((p) => p.name === name)) {
          setSel({ kind: "prj", name });
          setInspector(true);
        }
      },
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
      showRuns(name, kind, remote) {
        setSel({ kind, name, remote });
        setInspector(true);
        setInspectorTab("runs");
      },
      confirm,
    };
  }, [section, sel, inspector, inspectorTab, palette, theme, railAuto]);

  // arrow-key list navigation
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
      // leave arrows alone when focus is inside a menu/palette/dialog — Radix handles it
      const inOverlay =
        e.defaultPrevented ||
        !!el?.closest?.('[role="menu"],[role="listbox"],[role="dialog"],[cmdk-root]');
      // e.code is layout-independent — Ctrl+Л on a Russian layout
      // still reports code "KeyK" while e.key would be "л"
      if (e.ctrlKey && e.code === "KeyK") {
        e.preventDefault();
        setPalette((v) => !v);
      } else if (e.ctrlKey && e.code === "KeyI") {
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
        {/* inert kills focus/clicks under the palette — cheap aria-modal analog */}
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
                      {st && <CandidatesStrip />}
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
                      <ProjectsStrip />
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
            {/* paper: on a narrow window the inspector is a floating "sheet" over
                the content, on a wide one — a dock; the morph is animated via insets,
                radius and shadow, the element is not remounted */}
            {inspector && theme.startsWith("paper") && (
              <div
                className={`absolute z-30 overflow-hidden bg-(--bg-surface) ${inspDrag ? "" : "transition-[top,right,bottom,border-width,border-color,border-radius,box-shadow] duration-300 ease-(--ease-out)"} ${
                  inspDock
                    ? "top-0 right-0 bottom-0 rounded-none border-l border-(--border-hairline)"
                    : "top-3 right-3 bottom-3 rounded-xl border border-(--border-strong) elev"
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

        {dlg?.t === "service" && (
          <ServiceDialog spec={dlg.spec} isNew={dlg.isNew} />
        )}
        {dlg?.t === "project" && (
          <ProjectDialog spec={dlg.spec} isNew={dlg.isNew} />
        )}
        {dlg?.t === "onboarding" && <OnboardingDialog />}

        <Toaster
          theme={theme === "paper" ? "light" : "dark"}
          position="bottom-right"
          style={{ fontFamily: "inherit" }}
          toastOptions={{
            style: {
              background: "var(--bg-surface)",
              border: "1px solid var(--border-strong)",
              color: "var(--text-primary)",
              fontSize: "12px",
              borderRadius: "var(--radius-lg, 8px)",
              boxShadow: "var(--elev-shadow)",
            },
          }}
        />
      </TooltipProvider>
    </AppCtx.Provider>
  );
}
