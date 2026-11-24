import { useEffect, useState } from "react";
import { api, type ProcTarget, type ScannedProject } from "../../lib/api";
import { useApp, type Dlg } from "../../lib/ctx";
import { useT } from "../../lib/i18n";
import { refresh } from "../../lib/store";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { toast } from "sonner";

function msg(r: { ok: boolean; msg?: string }) {
  if (r.msg) toast(r.msg);
  return r;
}

/** Универсальный диалог подтверждения (стоп/удаление/чужой порт) */
export function ConfirmDialog({ d }: { d: Extract<Dlg, { t: "confirm" }> }) {
  const app = useApp();
  const t = useT();
  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{d.title}</DialogTitle>
          <DialogDescription className="selectable whitespace-pre-wrap">
            {d.body}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            variant={d.danger ? "danger" : "default"}
            onClick={() => {
              app.closeDlg();
              d.run();
            }}
          >
            {d.action}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/** Порт занят чужим процессом: убить и запустить */
export function PortConflictDialog({
  d,
}: {
  d: Extract<Dlg, { t: "portconflict" }>;
}) {
  const app = useApp();
  const t = useT();
  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t("PORT_BUSY_TITLE", { p: d.c.port })}</DialogTitle>
          <DialogDescription>
            {t("PORT_BUSY_DESC")}{" "}
            <span className="font-mono text-(--text-primary)">
              {d.c.pname} (pid {d.c.pid})
            </span>
            {d.c.suggest != null && (
              <span className="mt-1 block text-(--text-muted)">
                {t("NEAREST_FREE_PORT")}{" "}
                <span className="font-mono text-(--text-primary)">
                  :{d.c.suggest}
                </span>
              </span>
            )}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => {
              app.closeDlg();
              api.killPort(d.c.port).then(() => api.svcAction(d.name, "start"));
              toast(t("PORT_FREED_STARTING", { name: d.name }));
            }}
          >
            {t("KILL_AND_START")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function KillPortDialog() {
  const app = useApp();
  const t = useT();
  const [port, setPort] = useState("");
  const [targets, setTargets] = useState<ProcTarget[] | null>(null);
  const p = parseInt(port, 10);

  useEffect(() => {
    setTargets(null);
    if (!p || p < 1 || p > 65535) return;
    const t = window.setTimeout(() => {
      api.portTargets(p).then(setTargets).catch(() => setTargets([]));
    }, 300);
    return () => window.clearTimeout(t);
  }, [p]);

  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent
        className="max-w-sm"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT" && p && targets?.length) {
            e.preventDefault();
            app.closeDlg();
            app.killPortFlow(p);
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>{t("KILL_PORT_TITLE")}</DialogTitle>
          <DialogDescription>
            {t("KILL_LISTENERS_DESC")}
          </DialogDescription>
        </DialogHeader>
        <label className="block text-[11.5px] text-(--text-muted)">
          {t("PORT_FIELD")}
          <Input
            autoFocus
            inputMode="numeric"
            aria-label={t("PORT_FIELD")}
            className="font-mono mt-1"
            placeholder="20128"
            value={port}
            onChange={(e) => setPort(e.target.value.replace(/\D/g, ""))}
          />
        </label>
        {targets && (
          <div className="mt-2 font-mono text-[11.5px]">
            {targets.length === 0 && (
              <span className="text-(--text-muted)">{t("PORT_FREE")}</span>
            )}
            {targets.map((t) => (
              <div key={t.pid} className="text-(--text-secondary)">
                {t.name} <span className="text-(--text-muted)">pid {t.pid}</span>
              </div>
            ))}
          </div>
        )}
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            variant="danger"
            disabled={!p || !targets?.length}
            onClick={() => {
              app.closeDlg();
              app.killPortFlow(p);
            }}
          >
            {t("KILL")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function AutorunDialog({
  d,
}: {
  d: Extract<Dlg, { t: "autorun" }>;
}) {
  const app = useApp();
  const t = useT();
  const [name, setName] = useState(d.name);
  const [cmd, setCmd] = useState(d.cmd);
  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent
        className="max-w-md"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT" && name.trim() && cmd.trim()) {
            e.preventDefault();
            app.closeDlg();
            api.autorunSave(name.trim(), cmd.trim(), d.name).then(msg).then(() => refresh());
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>
            {d.name ? t("AUTORUN_ENTRY") : t("NEW_AUTORUN_ENTRY")}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          <label className="block text-[11.5px] text-(--text-muted)">
            {t("NAME")}
            <Input
              autoFocus
              className="mt-1"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label className="block text-[11.5px] text-(--text-muted)">
            {t("COMMAND")}
            <Input
              className="font-mono mt-1"
              placeholder={t("AUTORUN_CMD_PLACEHOLDER")}
              value={cmd}
              onChange={(e) => setCmd(e.target.value)}
            />
          </label>
        </div>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            disabled={!name.trim() || !cmd.trim()}
            onClick={() => {
              app.closeDlg();
              api
                .autorunSave(name.trim(), cmd.trim(), d.name)
                .then(msg)
                .then(() => refresh());
            }}
          >
            {t("SAVE")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function TokenDialog({ d }: { d: Extract<Dlg, { t: "token" }> }) {
  const app = useApp();
  const t = useT();
  const [value, setValue] = useState("");
  const [key, setKey] = useState("");
  useEffect(() => {
    api.serviceSpec(d.name).then((s) => setKey(s.env_key || "TOKEN"));
    api.serviceToken(d.name).then((r) => setValue(r.value));
  }, [d.name]);
  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent
        className="max-w-md"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT") {
            e.preventDefault();
            api.setServiceToken(d.name, value).then((r) => {
              if (r.ok) {
                toast(t("TOKEN_SAVED"));
                app.closeDlg();
              } else toast(r.msg || t("ERROR"));
            });
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>{t("TOKEN")} {key}</DialogTitle>
          <DialogDescription>{d.name}</DialogDescription>
        </DialogHeader>
        <Input
          autoFocus
          autoComplete="off"
          spellCheck={false}
          className="font-mono selectable"
          type="password"
          aria-label={t("TOKEN_VALUE")}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={t("TOKEN_VALUE")}
        />
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            onClick={() => {
              api.setServiceToken(d.name, value).then((r) => {
                if (r.ok) {
                  toast(t("TOKEN_SAVED"));
                  app.closeDlg();
                } else toast(r.msg || t("ERROR"));
              });
            }}
          >
            {t("WRITE")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ScanDialog({ d }: { d: Extract<Dlg, { t: "scan" }> }) {
  const app = useApp();
  const t = useT();
  const [checked, setChecked] = useState<Set<number>>(
    () => new Set(d.items.map((_, i) => i)),
  );
  const toggle = (i: number) =>
    setChecked((s) => {
      const n = new Set(s);
      if (n.has(i)) n.delete(i);
      else n.add(i);
      return n;
    });

  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t("FOUND_PROJECTS")}</DialogTitle>
          <DialogDescription>
            {t("FOUND_FOLDERS_COUNT", { n: d.items.length })}
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[300px] overflow-y-auto overscroll-contain rounded-md border border-(--border-hairline)">
          {d.items.map((p: ScannedProject, i: number) => (
            <label
              key={p.cwd}
              className="flex cursor-pointer items-center gap-2.5 border-b border-(--border-hairline) px-3 py-2 last:border-b-0 hover:bg-(--bg-hover)"
            >
              <input
                type="checkbox"
                checked={checked.has(i)}
                onChange={() => toggle(i)}
                className="accent-(--accent)"
              />
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5 truncate text-[12.5px] text-(--text-primary)">
                  <span className="truncate">{p.name}</span>
                  {p.framework && (
                    <span className="shrink-0 rounded bg-(--bg-hover) px-1 py-px text-[9.5px] text-(--text-muted)">
                      {p.framework}
                    </span>
                  )}
                  {p.branch && (
                    <span className="font-mono shrink-0 rounded bg-(--bg-hover) px-1 py-px text-[9.5px] text-(--text-muted)">
                      ⎇ {p.branch}
                    </span>
                  )}
                  {p.env_open && (
                    <span
                      title={t("ENV_IN_GIT_TIP")}
                      className="shrink-0 rounded bg-(--status-red)/12 px-1 py-px text-[9.5px] text-(--status-red)"
                    >
                      {t("ENV_IN_GIT")}
                    </span>
                  )}
                  {!!p.env_missing?.length && (
                    <span
                      title={t("ENV_MISSING_TIP", { list: p.env_missing.join(", ") })}
                      className="shrink-0 rounded bg-(--status-amber)/12 px-1 py-px text-[9.5px] text-(--status-amber)"
                    >
                      {p.env_missing.length === 1
                        ? t("MISSING_NAME", { name: p.env_missing[0] })
                        : t("MISSING_ENV_COUNT", { n: p.env_missing.length })}
                    </span>
                  )}
                </span>
                <span className="font-mono block truncate text-[11px] text-(--text-muted)">
                  {p.cwd}
                </span>
              </span>
              <span
                title={p.cmd}
                className="font-mono max-w-[160px] truncate text-[11px] text-(--text-secondary)"
              >
                {p.cmd}
              </span>
            </label>
          ))}
        </div>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button
            size="sm"
            disabled={checked.size === 0}
            onClick={() => {
              const items = d.items.filter((_, i) => checked.has(i));
              app.closeDlg();
              api.addProjects(items).then((r) => {
                toast(r.msg || t("ADDED_COUNT", { n: items.length }));
                refresh();
              });
            }}
          >
            {t("ADD_COUNT", { n: checked.size })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
