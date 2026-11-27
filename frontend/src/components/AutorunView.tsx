import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import type { AutorunRow } from "../lib/api";
import { api } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { refresh } from "../lib/store";
import { rowKeys, cn } from "../lib/utils";
import { SectionTitle, StatusDot } from "./bits";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown";
import { Switch } from "./ui/switch";

function ArRow({ row }: { row: AutorunRow }) {
  const app = useApp();
  const t = useT();
  return (
    <div
      {...rowKeys(() => app.openItem({ kind: "autorun", name: row.name }))}
      onClick={(e) => {
        if ((e.target as HTMLElement).closest("button")) return;
        app.openItem({ kind: "autorun", name: row.name });
      }}
      className={cn(
        "group flex h-[42px] cursor-pointer items-center gap-3 border-b border-(--border-hairline) px-3.5 select-none last:border-b-0 hover:bg-(--bg-hover)",
        app.sel?.kind === "autorun" && app.sel.name === row.name &&
          "bg-(--bg-selected)",
      )}
    >
      <Switch
        aria-label={t("AUTORUN_SWITCH", { name: row.name })}
        checked={row.arEnabled}
        onCheckedChange={(v) =>
          api.autorunToggle(row.name, v).then(() => refresh())
        }
      />
      <StatusDot state={row.arEnabled ? row.state : "off"} />
      <div className="min-w-0 flex-1">
        <div
          title={row.name}
          className="flex items-center gap-1.5 truncate text-[13px] font-medium text-(--text-primary)"
        >
          {row.name}
          {row.self && (
            <span className="shrink-0 text-[10px] font-medium text-(--text-muted)">
              {t("THIS_APP")}
            </span>
          )}
        </div>
        <div
          title={row.sub}
          className="font-mono truncate text-[11.5px] text-(--text-muted)"
        >
          {row.sub}
        </div>
      </div>
      <span
        title={row.metrics}
        className={cn(
          "w-[90px] shrink-0 truncate text-right text-[11.5px]",
          row.failed ? "text-(--status-amber)" : "text-(--text-muted)",
        )}
      >
        {row.metrics}
      </span>
      {!row.self && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={t("ACTIONS")}
              className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100"
            >
              <MoreHorizontal size={14} strokeWidth={1.75} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onSelect={() => app.editAutorun(row.name, row.sub, row.mine)}
            >
              <Pencil size={14} strokeWidth={1.75} /> {t("EDIT_ENTRY")}
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-(--status-red) data-[highlighted]:bg-(--bg-hover) data-[highlighted]:text-(--status-red)"
              onSelect={() => app.deleteAutorun(row.name)}
            >
              <Trash2 size={14} strokeWidth={1.75} /> {t("REMOVE_FROM_AUTORUN")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  );
}

function ArList({ rows }: { rows: AutorunRow[] }) {
  const t = useT();
  return (
    <div className="overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
      {rows.map((r) => (
        <ArRow key={r.name} row={r} />
      ))}
      {rows.length === 0 && (
        <div className="px-3.5 py-5 text-center text-[12px] text-(--text-muted)">
          {t("AUTORUN_EMPTY")}
        </div>
      )}
    </div>
  );
}

export function AutorunView({
  mine,
  other,
}: {
  mine: AutorunRow[];
  other: AutorunRow[];
}) {
  const app = useApp();
  const t = useT();
  return (
    <div>
      <SectionTitle
        right={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => app.openDlg({ t: "autorun", name: "", cmd: "" })}
          >
            {t("ADD_ENTRY")}
          </Button>
        }
      >
        {t("DASHBOARD_SERVICES")}
      </SectionTitle>
      <ArList rows={mine} />
      <SectionTitle className="mt-6">{t("THIRD_PARTY")}</SectionTitle>
      <ArList rows={other} />
    </div>
  );
}
