import { useEffect, useState } from "react";
import { Copy } from "lucide-react";
import { api, copyText, type ProcTarget } from "../../lib/api";
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

/** Generic confirmation dialog (stop/delete/foreign port) */
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

/** Port held by a foreign process: kill and start */
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
  const [free, setFree] = useState<{ port: number | null; from: number } | null>(null);
  const p = parseInt(port, 10);

  useEffect(() => {
    setTargets(null);
    const from = p >= 1 && p <= 65535 ? p : 8000;
    const t = window.setTimeout(() => {
      api.freePort(from).then(setFree).catch(() => setFree(null));
      if (from === p) {
        api.portTargets(p).then(setTargets).catch(() => setTargets([]));
      }
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
            placeholder="8080"
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
        {free && (
          <div className="mt-1 flex items-center gap-1 font-mono text-[11.5px] text-(--text-muted)">
            {t("NEAREST_FREE_PORT")}
            <span className="text-(--text-primary)">
              {free.port != null ? `:${free.port}` : "—"}
            </span>
            {free.port != null && (
              <button
                aria-label={t("COPY_PORT")}
                onClick={() => copyText(String(free.port))}
                className="cursor-pointer rounded-md p-0.5 hover:bg-(--bg-hover) hover:text-(--text-primary)"
              >
                <Copy size={12} strokeWidth={1.75} />
              </button>
            )}
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
