import {
  Code2,
  Copy,
  ExternalLink,
  GitBranch,
  FolderOpen,
  History,
  Loader2,
  MoreHorizontal,
  Pencil,
  Play,
  Square,
  Trash2,
} from "lucide-react";
import type { ProjectRow } from "../lib/api";
import { api } from "../lib/api";
import { useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { usePending } from "../lib/store";
import { rowKeys, cn } from "../lib/utils";
import { Chip, StatusDot } from "./bits";
import { Button } from "./ui/button";
import { Tip } from "./ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown";
import { toast } from "sonner";

export function ProjectCard({ row }: { row: ProjectRow }) {
  const app = useApp();
  const t = useT();
  const pend = usePending(row.name);
  const selected = app.sel?.kind === "prj" && app.sel.name === row.name;
  // open the URL only for a live project, otherwise the chip just copies
  const url =
    row.state === "up" && row.chipUrl && row.chipUrl !== "copy"
      ? row.chipUrl
      : "";
  // the project has a port/URL (configured or detected) — can be opened in a browser
  const link = row.chipUrl && row.chipUrl !== "copy" ? row.chipUrl : "";

  return (
    <div
      {...rowKeys(() => app.openItem({ kind: "prj", name: row.name }))}
      onClick={() => app.openItem({ kind: "prj", name: row.name })}
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
        <StatusDot state={row.state} />
      )}

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <button
            title={row.name}
            onClick={(e) => {
              e.stopPropagation();
              app.openItem({ kind: "prj", name: row.name });
            }}
            className="outline-none cursor-pointer truncate rounded text-left text-[13px] font-medium text-(--text-primary) focus-visible:ring-1 focus-visible:ring-(--accent)"
          >
            {row.name}
          </button>
          {row.failed && (
            <span className="text-[11px] text-(--status-red)">{t("STATE_CRASHED")}</span>
          )}
          {row.framework && (
            <span className="shrink-0 text-[10px] text-(--text-muted)">
              {row.framework}
            </span>
          )}
          {row.branch && (
            <span className="font-mono flex shrink-0 items-center gap-0.5 text-[10px] text-(--text-muted)">
              <GitBranch size={9} strokeWidth={1.75} />
              {row.branch}
            </span>
          )}
          {!!row.envMissing?.length && (
            <Tip
              label={[
                t("ENV_MISSING_TIP", { list: row.envMissing.join(", ") }),
                row.envExtra?.length
                  ? t("ENV_EXTRA", { list: row.envExtra.join(", ") })
                  : "",
                row.envEmpty?.length
                  ? t("ENV_EMPTY", { list: row.envEmpty.join(", ") })
                  : "",
              ]
                .filter(Boolean)
                .join(" · ")}
            >
              <span className="shrink-0 rounded bg-(--status-amber)/20 px-1 py-px text-[9.5px] font-medium text-(--status-amber)">
                {row.envMissing.length === 1
                  ? t("MISSING_NAME", { name: row.envMissing[0] })
                  : t("MISSING_ENV_COUNT", { n: row.envMissing.length })}
              </span>
            </Tip>
          )}
          {!row.envMissing?.length &&
            (!!row.envExtra?.length || !!row.envEmpty?.length) && (
            <Tip
              label={[
                row.envExtra?.length
                  ? t("ENV_UNDOCUMENTED", { list: row.envExtra.join(", ") })
                  : "",
                row.envEmpty?.length
                  ? t("ENV_EMPTY_VALUES", { list: row.envEmpty.join(", ") })
                  : "",
              ]
                .filter(Boolean)
                .join(" · ")}
            >
              <span className="shrink-0 text-[10px] text-(--text-muted)">
                ~ENV
              </span>
            </Tip>
          )}
          {row.envOpen && (
            <Tip label={t("ENV_IN_GIT_TIP")}>
              <span className="shrink-0 rounded bg-(--status-red)/20 px-1 py-px text-[9.5px] font-medium text-(--status-red)">
                {t("ENV_IN_GIT")}
              </span>
            </Tip>
          )}
        </div>
        <div
          title={pend ? undefined : row.sub}
          className="font-mono truncate text-[11.5px] text-(--text-secondary)"
        >
          {pend ? (
            <span className="text-(--accent-text)">
              {pend === "up" ? t("STARTING") : t("STOPPING")}
            </span>
          ) : (
            row.sub
          )}
        </div>
      </div>

      {row.chip && (
        <div className="flex shrink-0 items-center justify-end">
          <Chip
            text={row.chip}
            onClick={() => {
              if (url) api.openUrl(url);
              else {
                navigator.clipboard
                  .writeText(row.chip.replace(/^:/, ""))
                  .catch(() => {});
                toast(t("COPIED_CHIP", { chip: row.chip }));
              }
            }}
          />
        </div>
      )}

      <div className="w-[90px] shrink-0 text-right @max-[560px]:hidden">
        {row.m && (
          <span className="tnum inline-block font-mono text-[11px] text-(--text-secondary)">
            {row.m.mb} MB
          </span>
        )}
      </div>

      {/* quick actions; secondary ones (folder/IDE/link) on narrow —
          all of that is already in the ⋯ menu */}
      <div className="flex shrink-0 items-center justify-end gap-0.5">
        <div className="flex items-center gap-0.5 @max-[680px]:hidden">
        <Tip label={t("OPEN_FOLDER")}>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={t("OPEN_FOLDER")}
            className="opacity-40 group-hover:opacity-100 focus-visible:opacity-100"
            onClick={(e) => {
              e.stopPropagation();
              api.openProjectFolder(row.name);
            }}
          >
            <FolderOpen size={14} strokeWidth={1.75} />
          </Button>
        </Tip>
        <Tip label={t("OPEN_IN_IDE")}>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={t("OPEN_IN_IDE")}
            className="opacity-40 group-hover:opacity-100 focus-visible:opacity-100"
            onClick={(e) => {
              e.stopPropagation();
              api.openProjectIde(row.name);
            }}
          >
            <Code2 size={14} strokeWidth={1.75} />
          </Button>
        </Tip>
        {link && (
          <Tip label={link}>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={t("OPEN_IN_BROWSER")}
              className="opacity-40 group-hover:opacity-100 focus-visible:opacity-100"
              onClick={(e) => {
                e.stopPropagation();
                api.openUrl(link);
              }}
            >
              <ExternalLink size={14} strokeWidth={1.75} />
            </Button>
          </Tip>
        )}
        </div>
        {row.running ? (
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={t("STOP")}
            className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100 hover:text-(--status-red)"
            onClick={(e) => {
              e.stopPropagation();
              app.prjToggle(row.name);
            }}
          >
            <Square size={14} strokeWidth={1.75} />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={t("START")}
            className="opacity-60 group-hover:opacity-100 focus-visible:opacity-100 hover:text-(--status-green)"
            onClick={(e) => {
              e.stopPropagation();
              app.prjToggle(row.name);
            }}
          >
            <Play size={14} strokeWidth={1.75} />
          </Button>
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
            <DropdownMenuItem disabled={!url} onSelect={() => api.openUrl(url)}>
              <ExternalLink size={14} strokeWidth={1.75} /> {t("OPEN_LINK")}
            </DropdownMenuItem>
            <DropdownMenuItem
              disabled={!url}
              onSelect={() => {
                navigator.clipboard.writeText(url).catch(() => {});
                toast(t("COPIED"));
              }}
            >
              <Copy size={14} strokeWidth={1.75} /> {t("COPY_LINK")}
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => api.openPath(row.cwd)}>
              <FolderOpen size={14} strokeWidth={1.75} /> {t("OPEN_FOLDER")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => app.showRuns(row.name, "prj")}>
              <History size={14} strokeWidth={1.75} /> {t("RUN_HISTORY")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => app.editProject(row.name)}>
              <Pencil size={14} strokeWidth={1.75} /> {t("EDIT")}
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-(--status-red) data-[highlighted]:bg-(--bg-hover) data-[highlighted]:text-(--status-red)"
              onSelect={() => app.deleteProject(row.name, row.running)}
            >
              <Trash2 size={14} strokeWidth={1.75} /> {t("DELETE")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

export function ProjectsGrid({ rows }: { rows: ProjectRow[] }) {
  const t = useT();
  return (
    <div className="@container overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
      {rows.map((r) => (
        <ProjectCard key={r.name} row={r} />
      ))}
      {rows.length === 0 && (
        <div className="px-3.5 py-6 text-center text-[12px] text-(--text-muted)">
          {t("NO_PROJECTS")}
        </div>
      )}
    </div>
  );
}
