import { useEffect } from "react";
import { Command } from "cmdk";
import {
  Check,
  FolderGit2,
  Grid2x2,
  ListVideo,
  Network,
  OctagonAlert,
  Palette,
  PanelRight,
  Play,
  RotateCw,
  Server,
  Skull,
  Square,
} from "lucide-react";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { THEMES } from "../lib/theme";

export function CommandPalette() {
  const app = useApp();
  const t = useT();
  const st = useDash();

  useEffect(() => {
    if (!app.palette) return;
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        app.setPalette(false);
      }
    };
    window.addEventListener("keydown", h, true);
    return () => window.removeEventListener("keydown", h, true);
  }, [app.palette]);

  if (!app.palette || !st) return null;

  const run = (fn: () => void) => () => {
    app.setPalette(false);
    fn();
  };

  const svcs = [...st.services, ...st.remotes];

  return (
    <div
      className="scrim fixed inset-0 z-50 flex items-start justify-center bg-(--bg-scrim) pt-[15vh] backdrop-blur-[14px] backdrop-saturate-150 animate-[scrim-in_180ms_var(--ease-out)]"
      onMouseDown={() => app.setPalette(false)}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={t("COMMAND_PALETTE")}
        className="elev w-full max-w-[520px] overflow-hidden rounded-lg border border-(--border-strong) bg-(--bg-surface)"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <Command label={t("COMMAND_PALETTE")} loop>
          <div className="flex items-center gap-2 border-b border-(--border-hairline) px-3">
            <Command.Input
              autoFocus
              placeholder={t("SEARCH_PLACEHOLDER")}
              className="h-10 flex-1 bg-transparent text-[13px] text-(--text-primary) outline-none placeholder:text-(--text-muted)"
            />
          </div>
          <Command.List className="max-h-[340px] overflow-y-auto overscroll-contain p-1.5">
            <Command.Empty className="py-6 text-center text-[12px] text-(--text-muted)">
              {t("NOTHING_FOUND")}
            </Command.Empty>

            <Command.Group
              heading={<GroupHead>{t("COMMANDS")}</GroupHead>}
            >
              <Item value={`${t("START_ALL")} запустить все start all run`} onSelect={run(app.startAll)}>
                <Play size={14} strokeWidth={1.75} /> {t("START_ALL")}
              </Item>
              <Item value={`${t("STOP_ALL")} остановить все stop all`} onSelect={run(app.stopAll)}>
                <Square size={14} strokeWidth={1.75} /> {t("STOP_ALL")}
              </Item>
              <Item value={`${t("KILL_PORT")} освободить убить порт kill free port`} onSelect={run(() => app.openDlg({ t: "killport" }))}>
                <Skull size={14} strokeWidth={1.75} /> {t("KILL_PORT")}
              </Item>
              <Item value={`${t("FIND_FREE_PORT")} свободный порт free port find`} onSelect={run(() => app.openDlg({ t: "killport" }))}>
                <Network size={14} strokeWidth={1.75} /> {t("FIND_FREE_PORT")}
              </Item>
              <Item value={`${t("TOGGLE_INSPECTOR")} инспектор inspector toggle panel`} onSelect={run(() => app.setInspector(!app.inspector))}>
                <PanelRight size={14} strokeWidth={1.75} /> {t("TOGGLE_INSPECTOR")}
              </Item>
            </Command.Group>

            <Command.Group heading={<GroupHead>{t("THEME")}</GroupHead>}>
              {THEMES.map((th) => (
                <Item
                  key={th.id}
                  value={`тема theme ${th.label} ${t(th.label)}`}
                  onSelect={run(() => app.setTheme(th.id))}
                >
                  <Palette size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                  {t(th.label)}
                  {app.theme === th.id && (
                    <Check size={13} strokeWidth={1.75} className="ml-auto text-(--accent-text)" />
                  )}
                </Item>
              ))}
            </Command.Group>

            <Command.Group heading={<GroupHead>{t("SERVICES")}</GroupHead>}>
              {svcs.map((s) => (
                <Item
                  key={"s" + s.name}
                  value={`${s.name} ${s.chip} сервис service`}
                  onSelect={run(() => {
                    app.openItem({ kind: "svc", name: s.name, remote: s.remote });
                    app.setSection("infra");
                  })}
                >
                  <Server size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                  <span className="flex-1 truncate">{s.name}</span>
                  <span className="font-mono text-[11px] text-(--text-muted)">{s.chip}</span>
                </Item>
              ))}
              {svcs.filter((s) => !s.monitor).flatMap((s) => {
                const up = s.state === "up";
                return [
                  !up && (
                    <Item
                      key={"start" + s.name}
                      value={`запустить start ${s.name}`}
                      onSelect={run(() => app.svcToggle(s.name, s.remote))}
                    >
                      <Play size={14} strokeWidth={1.75} className="text-(--status-green)" />
                      {t("START_NAME", { name: s.name })}
                    </Item>
                  ),
                  up && (
                    <Item
                      key={"stop" + s.name}
                      value={`остановить stop ${s.name}`}
                      onSelect={run(() => app.svcToggle(s.name, s.remote))}
                    >
                      <Square size={14} strokeWidth={1.75} className="text-(--status-red)" />
                      {t("STOP_NAME", { name: s.name })}
                    </Item>
                  ),
                  up && (
                    <Item
                      key={"restart" + s.name}
                      value={`перезапустить restart ${s.name}`}
                      onSelect={run(() => app.svcRestart(s.name))}
                    >
                      <RotateCw size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                      {t("RESTART_NAME", { name: s.name })}
                    </Item>
                  ),
                ];
              })}
            </Command.Group>

            <Command.Group heading={<GroupHead>{t("SECTION_PROJECTS")}</GroupHead>}>
              {st.projects.map((p) => (
                <Item
                  key={"p" + p.name}
                  value={`${p.name} ${p.chip} проект project`}
                  onSelect={run(() => {
                    app.openItem({ kind: "prj", name: p.name });
                    app.setSection("projects");
                  })}
                >
                  <FolderGit2 size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                  <span className="flex-1 truncate">{p.name}</span>
                  <span className="font-mono text-[11px] text-(--text-muted)">{p.chip}</span>
                </Item>
              ))}
            </Command.Group>

            <Command.Group heading={<GroupHead>{t("SECTIONS")}</GroupHead>}>
              <Item value={`${t("SECTION_OVERVIEW")} обзор overview home`} onSelect={run(() => app.setSection("overview"))}>
                <Grid2x2 size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                {t("SECTION_OVERVIEW")}
              </Item>
              <Item value={`${t("SECTION_INFRA")} инфраструктура сервисы services infra`} onSelect={run(() => app.setSection("infra"))}>
                <Server size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                {t("SECTION_INFRA")}
              </Item>
              <Item value={`${t("SECTION_PROJECTS")} проекты projects`} onSelect={run(() => app.setSection("projects"))}>
                <FolderGit2 size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                {t("SECTION_PROJECTS")}
              </Item>
              <Item value={`${t("SECTION_PORTS")} порты ports`} onSelect={run(() => app.setSection("ports"))}>
                <Network size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                {t("SECTION_PORTS")}
              </Item>
              <Item value={`${t("SECTION_AUTORUN")} автозапуск autorun startup`} onSelect={run(() => app.setSection("autorun"))}>
                <ListVideo size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                {t("SECTION_AUTORUN")}
              </Item>
              <Item value={`${t("SECTION_EVENTS")} события events issues`} onSelect={run(() => app.setSection("events"))}>
                <OctagonAlert size={14} strokeWidth={1.75} className="text-(--text-muted)" />
                {t("SECTION_EVENTS")}
              </Item>
            </Command.Group>
          </Command.List>
          <div className="flex h-7 items-center gap-3 border-t border-(--border-hairline) px-3 text-[11px] text-(--text-muted) select-none">
            <span className="flex items-center gap-1">
              <kbd className="kbd">↑↓</kbd> {t("KBD_NAV")}
            </span>
            <span className="flex items-center gap-1">
              <kbd className="kbd">↵</kbd> {t("KBD_RUN")}
            </span>
            <span className="flex items-center gap-1">
              <kbd className="kbd">Esc</kbd> {t("KBD_CLOSE")}
            </span>
          </div>
        </Command>
      </div>
    </div>
  );
}

function GroupHead({ children }: { children: React.ReactNode }) {
  return (
    <span className="block px-2 pb-1 pt-2 text-[11px] font-medium uppercase tracking-[0.08em] text-(--text-muted)">
      {children}
    </span>
  );
}

function Item({
  children,
  ...props
}: React.ComponentPropsWithoutRef<typeof Command.Item>) {
  return (
    <Command.Item
      className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-[12.5px] text-(--text-secondary)"
      {...props}
    >
      {children}
    </Command.Item>
  );
}
