import {
  ExternalLink,
  FileText,
  FolderOpen,
  History,
  KeyRound,
  Loader2,
  MoreHorizontal,
  Pencil,
  Play,
  RotateCw,
  Server,
  Square,
  Trash2,
  Zap,
} from "lucide-react";
import type { ServiceRow } from "../lib/api";
import { api } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { usePending } from "../lib/store";
import { cn } from "../lib/utils";
import { Chip, StatusDot, WarnBadge } from "./bits";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown";
import { Tip } from "./ui/tooltip";

function ServiceRowItem({
  row,
  selected,
}: {
  row: ServiceRow;
  selected: boolean;
}) {
  const app = useApp();
  const t = useT();
  const pend = usePending(row.name);
  const running = row.state === "up";
  const remote = !!row.remote;
  const kind = remote ? "remote" : "svc";

  return (
    <div
      onClick={() => app.select({ kind: "svc", name: row.name, remote })}
      className={cn(
        "group relative flex h-[46px] cursor-pointer items-center gap-3 border-b border-(--border-hairline) px-3.5 last:border-b-0 select-none hover:bg-(--bg-hover)",
        selected && "bg-(--bg-selected) hover:bg-(--bg-selected)",
      )}
    >
      {selected && (
        <span className="absolute inset-y-0 left-0 w-[2px] bg-(--accent)" />
      )}

      {pend ? (
        <Loader2 size={10} strokeWidth={2} className="shrink-0 animate-spin text-(--accent-text)" />
      ) : (
        <StatusDot state={row.state} warn={row.warn} />
      )}

      {/* имя + описание */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <button
            title={row.name}
            onClick={(e) => {
              e.stopPropagation();
              app.select({ kind: "svc", name: row.name, remote });
            }}
            className="outline-none cursor-pointer truncate rounded text-left text-[13px] font-medium text-(--text-primary) focus-visible:ring-1 focus-visible:ring-(--accent)"
          >
            {row.name}
          </button>
          {row.inAutorun && (
            <Tip label={t("IN_AUTORUN")}>
              <Zap size={12} strokeWidth={1.75} className="text-(--text-muted)" />
            </Tip>
          )}
          {row.monitor && (
            <Tip label={t("MONITOR_ONLY")}>
              <ExternalLink size={11} strokeWidth={1.75} className="text-(--text-muted)" />
            </Tip>
          )}
        </div>
        <div title={row.sub || undefined}
          className="truncate text-[11.5px] text-(--text-secondary)">
          {pend ? (
            <span className="text-(--accent-text)">
              {pend === "up" ? t("STARTING") : t("STOPPING")}
            </span>
          ) : row.failed && row.reason ? (
            <span className="text-(--status-red)">
              {row.reason === "circuit_open" ? t("CRASH_LOOP") : row.reason}
            </span>
          ) : (
            row.sub || row.pillText
          )}
        </div>
      </div>

      {/* порт / ip */}
      <div className="flex w-[130px] shrink items-center justify-end gap-1.5">
        {row.envWarn && <WarnBadge text={row.envWarn} />}
        {row.warn && !row.envWarn && (
          <WarnBadge text={row.metrics || row.sub || t("STATE_OFF")} />
        )}
        {row.chip && (
          <Chip text={row.chip} onClick={() => app.chip(kind, row.name)} />
        )}
      </div>

      {/* метрики — на узком окне прячем, имя важнее */}
      <div className="w-[120px] shrink-0 text-right font-mono text-[12px] text-(--text-secondary) max-[1100px]:hidden">
        {row.m ? (
          <span>
            {row.m.mb} MB{row.m.up ? ` · ${row.m.up}` : ""}
          </span>
        ) : (
          <span className="text-(--text-muted)">
            {row.warn ? "" : row.metrics || ""}
          </span>
        )}
      </div>

      {/* действия */}
      <div className="flex w-[88px] shrink-0 items-center justify-end gap-0.5">
        {!row.monitor && (
          <>
            {running ? (
              <Tip label={t("STOP")}>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100 hover:text-(--status-red)"
                  onClick={(e) => {
                    e.stopPropagation();
                    app.svcToggle(row.name, remote);
                  }}
                >
                  <Square size={14} strokeWidth={1.75} fill="currentColor" />
                </Button>
              </Tip>
            ) : (
              <Tip label={t("START")}>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100 hover:text-(--status-green)"
                  onClick={(e) => {
                    e.stopPropagation();
                    app.svcToggle(row.name, remote);
                  }}
                >
                  <Play size={14} strokeWidth={1.75} />
                </Button>
              </Tip>
            )}
            {running && (
              <Tip label={t("RESTART")}>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation();
                    app.svcRestart(row.name);
                  }}
                >
                  <RotateCw size={14} strokeWidth={1.75} />
                </Button>
              </Tip>
            )}
          </>
        )}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={t("ACTIONS")}
              className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal size={14} strokeWidth={1.75} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={() => api.openServiceLog(row.name)}>
              <FileText size={14} strokeWidth={1.75} /> {t("LAUNCH_LOG")}
            </DropdownMenuItem>
            {row.hasToken && (
              <DropdownMenuItem
                onSelect={() => app.openDlg({ t: "token", name: row.name })}
              >
                <KeyRound size={14} strokeWidth={1.75} /> {t("TOKEN")}
              </DropdownMenuItem>
            )}
            {row.hasUrl && (
              <DropdownMenuItem
                onSelect={async () => {
                  const s = await api.serviceSpec(row.name);
                  if (s.url) api.openUrl(s.url);
                }}
              >
                <ExternalLink size={14} strokeWidth={1.75} /> {t("OPEN_LINK")}
              </DropdownMenuItem>
            )}
            {row.hasPath && (
              <DropdownMenuItem
                onSelect={async () => {
                  const s = await api.serviceSpec(row.name);
                  if (s.path) api.openPath(s.path);
                }}
              >
                <FolderOpen size={14} strokeWidth={1.75} /> {t("OPEN_FOLDER")}
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => app.showRuns(row.name, "svc")}>
              <History size={14} strokeWidth={1.75} /> {t("RUN_HISTORY")}
            </DropdownMenuItem>
            {!row.monitor && (
              <DropdownMenuCheckboxItem
                checked={row.autorestart}
                onCheckedChange={(v) =>
                  api.setAutorestart(row.name, !!v).then(() => undefined)
                }
              >
                {t("RESTART_ON_CRASH")}
              </DropdownMenuCheckboxItem>
            )}
            <DropdownMenuItem onSelect={() => app.editService(row.name)}>
              <Pencil size={14} strokeWidth={1.75} /> {t("EDIT")}
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-(--status-red) data-[highlighted]:bg-(--bg-hover) data-[highlighted]:text-(--status-red)"
              onSelect={() => app.deleteService(row.name)}
            >
              <Trash2 size={14} strokeWidth={1.75} /> {t("DELETE")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

export function ServiceList({ rows }: { rows: ServiceRow[] }) {
  const app = useApp();
  const t = useT();
  return (
    <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
      {rows.map((r) => (
        <ServiceRowItem
          key={r.name}
          row={r}
          selected={
            app.sel?.kind === "svc" &&
            app.sel.name === r.name &&
            !!app.sel.remote === !!r.remote
          }
        />
      ))}
      {rows.length === 0 && (
        <div className="flex flex-col items-center gap-2 px-3.5 py-8">
          <Server size={18} strokeWidth={1.5} className="text-(--text-muted)" />
          <div className="text-[12px] text-(--text-muted)">
            {t("NO_SERVICES")}
          </div>
        </div>
      )}
    </div>
  );
}
