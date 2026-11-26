import { useEffect, useState } from "react";
import { ExternalLink, FolderOpen, FolderPlus, GraduationCap, RefreshCw, X } from "lucide-react";
import { api, type AppSettings } from "../lib/api";
import { useApp } from "../lib/ctx";
import { LANGS, setLang, useT } from "../lib/i18n";
import { useCached, useDash } from "../lib/store";
import { cn } from "../lib/utils";
import { toast } from "sonner";
import { SectionTitle, ThemePicker } from "./bits";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Switch } from "./ui/switch";

/** Settings row: label+hint on the left, control on the right (VS Code style) */
function Row({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-[46px] flex-wrap items-center gap-x-4 gap-y-1.5 border-b border-(--border-hairline) px-3.5 py-2 last:border-b-0">
      <div className="min-w-0 flex-1 basis-40">
        <div className="text-[13px] text-(--text-primary)">{label}</div>
        {hint && (
          <div className="mt-0.5 text-[11.5px] leading-snug text-(--text-muted)">
            {hint}
          </div>
        )}
      </div>
      <div className="flex min-w-0 flex-wrap items-center justify-end gap-2">
        {children}
      </div>
    </div>
  );
}

function LabelRow({
  title,
  items,
  onRemove,
}: {
  title: string;
  items: string[];
  onRemove: (x: string) => void;
}) {
  const t = useT();
  return (
    <div className="border-b border-(--border-hairline) px-3.5 py-2 last:border-b-0">
      <div className="text-[11px] text-(--text-muted)">{title}</div>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {items.map((x) => (
          <span
            key={x}
            className="flex items-center gap-1 rounded bg-(--border-hairline) px-1.5 py-0.5 font-mono text-[11px] text-(--text-secondary)"
          >
            {x}
            <button
              onClick={() => onRemove(x)}
              aria-label={`${t("REMOVE")} ${x}`}
              className="cursor-pointer text-(--text-muted) hover:text-(--status-red)"
            >
              <X size={11} strokeWidth={2} />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

function Group({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
      {children}
    </div>
  );
}

export function SettingsView() {
  const app = useApp();
  const t = useT();
  const st = useDash();
  const [srv, setSrv] = useCached<AppSettings>("settings");
  const [probe, setProbe] = useState(() =>
    srv ? String(srv.probe_interval) : "",
  );
  const [depT, setDepT] = useState(() => (srv ? String(srv.dep_timeout) : ""));
  const [backoff, setBackoff] = useState(() => srv?.backoff.join(", ") ?? "");
  const [roots, setRoots] = useState<string[]>(() => srv?.scan_roots ?? []);
  // update check: "wait" → fetching; {tag,url} → newer release found
  const [upd, setUpd] = useState<{ tag: string; url: string } | "wait" | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    const had = srv !== null;
    api.settings().then((s) => {
      setSrv(s);
      if (!had) {
        // first-ever load fills the form; on remounts it already holds
        // (cached) values — refilling would clobber in-flight typing
        setProbe(String(s.probe_interval));
        setDepT(String(s.dep_timeout));
        setBackoff(s.backoff.join(", "));
        setRoots(s.scan_roots);
      }
    });
  }, []);

  const saveRoots = (next: string[]) => {
    setRoots(next);
    api.saveSettings({ scan_roots: next }).then((r) => {
      if (r.ok) (setSrv(r), setRoots(r.scan_roots));
      else toast(r.msg || t("SAVE_FAILED"));
    });
  };
  const addRoot = () =>
    api.pickDir(roots[roots.length - 1] || "").then((r) => {
      if (r.dir && !roots.includes(r.dir)) saveRoots([...roots, r.dir]);
    });

  const saveBackend = () => {
    const bo = backoff
      .split(/[,\s]+/)
      .map((x) => parseFloat(x))
      .filter((x) => !isNaN(x));
    api
      .saveSettings({
        probe_interval: parseFloat(probe),
        dep_timeout: parseFloat(depT),
        backoff: bo,
      })
      .then((r) => {
        if (r.ok) {
          setSrv(r);
          setProbe(String(r.probe_interval));
          setDepT(String(r.dep_timeout));
          setBackoff(r.backoff.join(", "));
          toast(t("SETTINGS_APPLIED"));
        } else toast(r.msg || t("SAVE_FAILED"));
      });
  };

  const num = (v: string) =>
    /^-?\d*\.?\d*$/.test(v) ? v : v.replace(/[^\d.]/g, "");

  const doUpdate = async () => {
    setUpdating(true);
    const r = await api.selfUpdate().catch(() => null);
    if (r?.ok) {
      toast(t("UPDATE_RESTARTING"));
      // the app exits and relaunches itself — nothing more to do
    } else {
      setUpdating(false);
      toast.error(r?.msg || t("UPDATE_FAILED"));
    }
  };

  const checkUpdates = async () => {
    setUpd("wait");
    try {
      const r = await fetch(
        "https://api.github.com/repos/dvinerlove/dev-dashboard/releases/latest",
        { signal: AbortSignal.timeout(8000) },
      );
      if (!r.ok) throw new Error(`${r.status}`);
      const j = (await r.json()) as { tag_name?: string; html_url?: string };
      const tag = String(j.tag_name ?? "").replace(/^v/, "");
      if (!tag || !j.html_url) throw new Error("bad release");
      const cur = (st?.version ?? "0").split(".").map((x) => parseInt(x, 10) || 0);
      const nxt = tag.split(".").map((x) => parseInt(x, 10) || 0);
      let newer = false;
      for (let i = 0; i < Math.max(cur.length, nxt.length); i++) {
        const d = (nxt[i] ?? 0) - (cur[i] ?? 0);
        if (d) {
          newer = d > 0;
          break;
        }
      }
      if (newer) setUpd({ tag, url: j.html_url });
      else {
        setUpd(null);
        toast(t("UPDATE_LATEST"));
      }
    } catch {
      setUpd(null);
      toast.error(t("UPDATE_FAILED"));
    }
  };

  return (
    <>
      <SectionTitle>{t("APPEARANCE")}</SectionTitle>
      <Group>
        <div className="border-b border-(--border-hairline) px-3.5 py-3 last:border-b-0">
          <div className="text-[13px] text-(--text-primary)">{t("THEME")}</div>
          <div className="mt-0.5 text-[11.5px] leading-snug text-(--text-muted)">
            {t("APPLIES_INSTANTLY")}
          </div>
          <ThemePicker className="mt-2.5 grid-cols-3" />
        </div>
        <Row label={t("LANGUAGE")} hint={t("LANG_AUTO_HINT")}>
          {["auto", ...LANGS].map((l) => (
            <button
              key={l}
              onClick={() =>
                api.saveSettings({ lang: l }).then((r) => {
                  if (r.ok) {
                    setSrv(r);
                    if (r.lang_resolved) setLang(r.lang_resolved);
                  }
                })
              }
              className={cn(
                "cursor-pointer rounded-md border px-2.5 py-1 text-[12px] transition-colors",
                (srv?.lang ?? "auto") === l
                  ? "border-(--accent) bg-(--bg-selected) text-(--text-primary)"
                  : "border-(--border-hairline) text-(--text-secondary) hover:border-(--border-strong)",
              )}
            >
              {l === "auto" ? t("LANG_AUTO") : l.toUpperCase()}
            </button>
          ))}
        </Row>
        <Row
          label={t("SIDEBAR_AUTO_COLLAPSE")}
          hint={t("SIDEBAR_AUTO_HINT")}
        >
          <Switch
            checked={app.railAuto}
            onCheckedChange={app.setRailAuto}
            aria-label={t("SIDEBAR_AUTO_COLLAPSE")}
          />
        </Row>
        <Row
          label={t("INSPECTOR_PANEL")}
          hint={t("INSPECTOR_PANEL_HINT")}
        >
          <Switch
            checked={app.inspector}
            onCheckedChange={app.setInspector}
            aria-label={t("INSPECTOR_PANEL")}
          />
        </Row>
      </Group>

      <SectionTitle className="mt-4">{t("MONITORING")}</SectionTitle>
      <Group>
        <Row
          label={t("POLL_INTERVAL")}
          hint={t("POLL_INTERVAL_HINT")}
        >
          <Input
            value={probe}
            onChange={(e) => setProbe(num(e.target.value))}
            className="w-20 text-right font-mono"
            inputMode="decimal"
            aria-label={t("POLL_INTERVAL_ARIA")}
          />
        </Row>
        <Row
          label={t("DEP_TIMEOUT")}
          hint={t("DEP_TIMEOUT_HINT")}
        >
          <Input
            value={depT}
            onChange={(e) => setDepT(num(e.target.value))}
            className="w-20 text-right font-mono"
            inputMode="decimal"
            aria-label={t("DEP_TIMEOUT_ARIA")}
          />
        </Row>
        <Row
          label={t("RESTART_BACKOFF")}
          hint={t("BACKOFF_DELAYS_HINT")}
        >
          <Input
            value={backoff}
            onChange={(e) => setBackoff(e.target.value)}
            className="w-44 text-right font-mono"
            placeholder="2, 5, 10, 20"
            aria-label={t("BACKOFF_DELAYS_ARIA")}
          />
        </Row>
        <div className="flex min-h-[46px] items-center justify-end border-b border-(--border-hairline) px-3.5 py-2 last:border-b-0">
          <Button
            size="sm"
            onClick={saveBackend}
            disabled={!srv}
            className="h-7"
          >
            {t("APPLY")}
          </Button>
        </div>
      </Group>

      <SectionTitle className="mt-4">{t("PROJECT_FOLDERS")}</SectionTitle>
      <Group>
        {roots.length === 0 && !!srv?.scan_roots_auto?.length && (
          <div className="border-b border-(--border-hairline) px-3.5 py-2 text-[11.5px] text-(--text-muted) last:border-b-0">
            {t("SCAN_ROOTS_AUTO", {
              dirs: srv.scan_roots_auto.join(", "),
            })}
          </div>
        )}
        {roots.map((r) => (
          <div
            key={r}
            className="flex items-center gap-2.5 border-b border-(--border-hairline) px-3.5 py-2 last:border-b-0"
          >
            <FolderOpen
              size={14}
              strokeWidth={1.75}
              className="shrink-0 text-(--accent)"
            />
            <span
              className="min-w-0 flex-1 truncate font-mono text-[12px] text-(--text-secondary)"
              title={r}
            >
              {r}
            </span>
            <button
              onClick={() => saveRoots(roots.filter((x) => x !== r))}
              aria-label={t("REMOVE_FOLDER")}
              className="shrink-0 cursor-pointer rounded p-0.5 text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--status-red)"
            >
              <X size={13} strokeWidth={2} />
            </button>
          </div>
        ))}
        <button
          onClick={addRoot}
          className="flex w-full cursor-pointer items-center gap-2 px-3.5 py-2.5 text-[12.5px] text-(--text-secondary) transition-colors hover:text-(--accent-text)"
        >
          <FolderPlus size={14} strokeWidth={1.75} /> {t("ADD_FOLDER")}
          <span className="text-(--text-muted)">
            {t("FOLDERS_HINT")}
          </span>
        </button>
      </Group>

      <SectionTitle className="mt-4">{t("PORT_MARKS")}</SectionTitle>
      <Group>
        {srv?.port_mine.length ? (
          <LabelRow
            title={t("MINE_COUNTED_OURS")}
            items={srv.port_mine}
            onRemove={(x) =>
              api
                .saveSettings({
                  port_mine: srv.port_mine.filter((p) => p !== x),
                })
                .then((r) => setSrv(r))
            }
          />
        ) : null}
        {srv?.port_hidden.length ? (
          <LabelRow
            title={t("HIDDEN_PORTS_TITLE")}
            items={srv.port_hidden}
            onRemove={(x) =>
              api
                .saveSettings({
                  port_hidden: srv.port_hidden.filter((p) => p !== x),
                })
                .then((r) => setSrv(r))
            }
          />
        ) : null}
        {!srv?.port_mine.length && !srv?.port_hidden.length && (
          <div className="px-3.5 py-2.5 text-[12px] text-(--text-muted)">
            {t("PORT_MARKS_HINT")}
          </div>
        )}
      </Group>

      <SectionTitle className="mt-4">{t("APP_SECTION")}</SectionTitle>
      <Group>
        <Row
          label={t("START_WITH_WINDOWS")}
          hint={t("START_WITH_WINDOWS_HINT")}
        >
          <Switch
            checked={srv?.autostart ?? false}
            disabled={!srv}
            onCheckedChange={(v) =>
              api.saveSettings({ autostart: v }).then((r) => {
                if (r.ok) setSrv(r);
                else toast(r.msg || t("SAVE_FAILED"));
              })
            }
            aria-label={t("START_WITH_WINDOWS")}
          />
        </Row>
        <Row
          label="API"
          hint={t("API_PORT_HINT")}
        >
          <span className="font-mono text-[12px] text-(--text-secondary)">
            127.0.0.1:{srv?.api_port ?? "…"}
          </span>
        </Row>
        <Row
          label={t("CONFIGS")}
          hint={srv ? srv.config_dir : "…"}
        >
          <Button
            variant="secondary"
            size="sm"
            className="h-7"
            disabled={!srv}
            onClick={() => srv && api.openPath(srv.config_dir)}
          >
            <FolderOpen size={14} strokeWidth={1.75} /> {t("OPEN")}
          </Button>
        </Row>
        <Row
          label={t("TUTORIAL")}
          hint={t("TUTORIAL_HINT")}
        >
          <Button
            variant="secondary"
            size="sm"
            className="h-7"
            onClick={() => app.openDlg({ t: "onboarding" })}
          >
            <GraduationCap size={14} strokeWidth={1.75} /> {t("SHOW_AGAIN")}
          </Button>
        </Row>
        <Row label={t("VERSION")}>
          <span className="font-mono text-[12px] text-(--text-secondary)">
            Dev Dashboard v{st?.version ?? "…"}
          </span>
          {upd && upd !== "wait" ? (
            <>
              {st?.updChannel !== "dev" && (
                <Button
                  size="sm"
                  className="h-7"
                  disabled={updating}
                  onClick={doUpdate}
                >
                  <RefreshCw
                    size={13}
                    strokeWidth={1.75}
                    className={updating ? "animate-spin" : ""}
                  />{" "}
                  {t("UPDATE_NOW")}
                </Button>
              )}
              <Button
                variant="secondary"
                size="sm"
                className="h-7"
                onClick={() => api.openUrl(upd.url)}
              >
                <ExternalLink size={13} strokeWidth={1.75} />{" "}
                {t("UPDATE_AVAILABLE", { v: upd.tag })}
              </Button>
            </>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              className="h-7"
              disabled={upd === "wait"}
              onClick={checkUpdates}
            >
              <RefreshCw size={13} strokeWidth={1.75} /> {t("CHECK_UPDATES")}
            </Button>
          )}
        </Row>
      </Group>
    </>
  );
}
