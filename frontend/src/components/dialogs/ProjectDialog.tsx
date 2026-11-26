import { useState } from "react";
import { FolderOpen } from "lucide-react";
import type { ProjectSpec } from "../../lib/api";
import { api } from "../../lib/api";
import { useApp } from "../../lib/ctx";
import { useT } from "../../lib/i18n";
import { refresh } from "../../lib/store";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Switch } from "../ui/switch";
import { toast } from "sonner";

export function ProjectDialog({
  spec,
  isNew,
}: {
  spec: ProjectSpec | null;
  isNew?: boolean;
}) {
  const app = useApp();
  const t = useT();
  const s = spec ?? {};
  // scanned spec is new: name pre-fills the form, not the rename key
  const oldName = spec && !isNew ? (s.name ?? "") : "";
  const [f, setF] = useState({
    name: s.name ?? "",
    cmd: s.cmd ?? "",
    cwd: s.cwd ?? "",
    url: s.url ?? "",
    autostart: !!s.autostart,
  });
  const valid = !!(f.name.trim() && f.cmd.trim() && f.cwd.trim());
  const save = () => {
    const d: ProjectSpec = {
      name: f.name.trim(),
      cmd: f.cmd.trim(),
      cwd: f.cwd.trim(),
    };
    if (f.url.trim()) d.url = f.url.trim();
    if (f.autostart) d.autostart = true;
    api.saveProject(oldName, d).then((r) => {
      if (!r.ok) return toast(r.msg || t("ERROR"));
      app.closeDlg();
      refresh();
    });
  };

  return (
    <Dialog open onOpenChange={(v) => !v && app.closeDlg()}>
      <DialogContent
        className="max-w-md"
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.nativeEvent.isComposing && (e.target as HTMLElement).tagName === "INPUT" && valid) {
            e.preventDefault();
            save();
          }
        }}
      >
        <DialogHeader>
          <DialogTitle>
            {oldName ? t("EDIT_PROJECT") : t("NEW_PROJECT")}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          <label className="block text-[11.5px] text-(--text-muted)">
            {t("NAME_REQUIRED")}
            <Input
              autoFocus
              className="mt-1"
              value={f.name}
              onChange={(e) => setF({ ...f, name: e.target.value })}
            />
          </label>
          <label className="block text-[11.5px] text-(--text-muted)">
            {t("COMMAND_REQUIRED")}
            <Input
              className="font-mono mt-1"
              placeholder="npm run dev"
              value={f.cmd}
              onChange={(e) => setF({ ...f, cmd: e.target.value })}
            />
          </label>
          <div className="block text-[11.5px] text-(--text-muted)">
            <label htmlFor="prj-cwd">{t("FOLDER_REQUIRED")}</label>
            <span className="mt-1 flex gap-1.5">
              <Input
                id="prj-cwd"
                className="font-mono flex-1"
                value={f.cwd}
                onChange={(e) => setF({ ...f, cwd: e.target.value })}
              />
              <Button
                variant="outline"
                size="icon"
                aria-label={t("PICK_FOLDER")}
                onClick={() =>
                  api.pickDir(f.cwd).then((r) => {
                    if (r.dir) setF((p) => ({ ...p, cwd: r.dir }));
                  })
                }
              >
                <FolderOpen size={14} strokeWidth={1.75} />
              </Button>
            </span>
          </div>
          <label className="block text-[11.5px] text-(--text-muted)">
            {t("URL_FIELD")}
            <Input
              className="font-mono mt-1"
              placeholder="http://localhost:5173"
              value={f.url}
              onChange={(e) => setF({ ...f, url: e.target.value })}
            />
          </label>
          <label className="flex cursor-pointer items-center gap-2 pt-1 text-[12px] text-(--text-secondary)">
            <Switch
              aria-label={t("LAUNCH_WITH_DASHBOARD")}
              checked={f.autostart}
              onCheckedChange={(v) => setF({ ...f, autostart: v })}
            />
            {t("LAUNCH_WITH_DASHBOARD")}
          </label>
        </div>
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={app.closeDlg}>
            {t("CANCEL")}
          </Button>
          <Button size="sm" disabled={!valid} onClick={save}>
            {t("SAVE")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
