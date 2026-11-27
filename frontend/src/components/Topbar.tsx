import { useEffect, useRef, useState } from "react";
import {
  CircleArrowDown,
  Minus,
  PanelRight,
  Search,
  Square,
  X,
} from "lucide-react";
import { api } from "../lib/api";
import { SECTION_TITLES, useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { installUpdate, useUpdateInfo } from "../lib/update";
import { cn, winCtl } from "../lib/utils";
import { Button } from "./ui/button";
import { Tip } from "./ui/tooltip";

/** stop mousedown here — otherwise buttons inside the topbar
 *  would also start dragging the window */
const noDrag = (e: React.MouseEvent) => e.stopPropagation();

/** LMB on the topbar → native Windows move loop (one call, no
 *  .pywebview-drag-region lag). detail>1 is a double click → maximize, not drag. */
const startDrag = (e: React.MouseEvent) => {
  if (e.button === 0 && e.detail < 2) winCtl("window_drag_start")();
};

/** Double click on the topbar → maximize, but not through buttons: dblclick
 *  bubbles; without the gate a double click on any button would maximize */
const dblMax = (e: React.MouseEvent) => {
  if (!(e.target as HTMLElement).closest("button, a, input, [role=button]")) {
    winCtl("window_toggle_maximize")();
  }
};

export function Topbar() {
  const app = useApp();
  const t = useT();
  const st = useDash();
  const issues = st?.issues ?? 0;
  const problems = st?.problems.length ?? 0;
  const bad = problems > 0;
  const upd = useUpdateInfo();

  const installClick = () => {
    if (!upd) return;
    // dev runs can't self-update — the release page is the next best thing
    if (st?.updChannel === "dev") return void api.openUrl(upd.url);
    app.confirm(
      t("UPDATE_AVAILABLE", { v: upd.tag }),
      t("UPDATE_CONFIRM_BODY"),
      t("UPDATE_NOW"),
      () => void installUpdate(),
    );
  };

  // search strictly centered in the window: absolute + measured free space
  // between the edge blocks (ResizeObserver catches both resizes and
  // title/status collapses) → the center is exact, cannot overlap,
  // and transition-[width] turns width changes into a smooth drift
  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLButtonElement>(null);
  const [free, setFree] = useState(600);
  useEffect(() => {
    const lastF = { cur: 9999 };
    const measure = () => {
      const l = leftRef.current?.getBoundingClientRect();
      const r = rightRef.current?.getBoundingClientRect();
      const btn = searchRef.current;
      if (!l || !r || !btn) return;
      const hdrLeft = l.left - 12;             // px-3
      const cx = (l.left + r.right) / 2;
      const half = Math.min(r.left - cx, cx - l.right);
      const f = Math.max(0, half * 2 - 16);
      const w = Math.min(340, f);
      const wEff = f < 92 ? Math.min(32, f) : w;
      // the button wants the center but moves into a free gap when neighbors
      // cross it during their own collapses — overlapping is not allowed
      const lo = l.right + 8;
      const hi = r.left - 8 - wEff;
      const x = Math.min(Math.max(cx - wEff / 2, lo), Math.max(hi, lo));
      const hide = wEff < 40;
      // collapse/evacuation — instant (a transition would smear across frames);
      // expand and return to center — smooth
      btn.style.transitionProperty = f < lastF.cur ? "none" : "";
      lastF.cur = f;
      btn.style.width = `${wEff}px`;
      btn.style.left = `${x - hdrLeft}px`;
      btn.style.opacity = hide ? "0" : "1";
      btn.style.pointerEvents = hide ? "none" : "";
      setFree(f);
    };
    // RO on the blocks catches content changes (collapses, badges);
    // on window resize the sizes are the same — positions shift, need resize
    const ro = new ResizeObserver(measure);
    for (const e of [leftRef.current, rightRef.current]) {
      if (e) ro.observe(e);
    }
    window.addEventListener("resize", measure);
    measure();
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);
  const searchW = Math.min(340, free);
  // three modes: text pill / kbd pill / bare icon (edge case)
  const mode = searchW >= 190 ? "full" : searchW >= 92 ? "kbd" : "icon";
  const effW = mode === "icon" ? 32 : searchW;

  return (
    <header
      onMouseDown={startDrag}
      onDoubleClick={dblMax}
      className={cn(
        "relative flex h-10 shrink-0 items-center gap-3 border-b border-(--border-hairline) bg-(--bg-base) px-3 select-none",
      )}
    >
      <div
        ref={leftRef}
        className="flex items-center gap-2 whitespace-nowrap"
      >
        <h1 className="sr-only">{t(SECTION_TITLES[app.section])}</h1>
      </div>

      {/* search → Command Palette: strictly centered, width = measured free
          space, collapses to an icon when tight */}
      <button
        ref={searchRef}
        onClick={() => app.setPalette(true)}
        onMouseDown={noDrag}
        aria-label={t("SEARCH_CTRL_K")}
        style={{ width: effW }}
        className={cn(
          "absolute top-1/2 left-0 flex h-7 min-w-0 -translate-y-1/2 cursor-pointer items-center gap-2 overflow-hidden rounded-md border border-(--border-hairline) bg-(--bg-surface) px-2.5 text-[12px] text-(--text-muted) transition-[width,left,opacity,color,background-color,border-color] hover:border-(--border-strong)",
          mode !== "full" && "justify-center",
        )}
      >
        <Search size={14} strokeWidth={1.75} className="shrink-0" />
        {mode === "full" && (
          <span className="flex-1 truncate text-left">
            {t("SEARCH_PLACEHOLDER_SHORT")}
          </span>
        )}
        {mode !== "icon" && <kbd className="kbd">Ctrl+K</kbd>}
      </button>

      <div
        ref={rightRef}
        onMouseDown={noDrag}
        className="ml-auto flex items-center gap-1.5"
      >
        {/* update available — passive startup check found a newer release */}
        {upd && (
          <Tip label={t("UPDATE_AVAILABLE", { v: upd.tag })}>
            <Button
              variant="ghost"
              size="icon"
              aria-label={t("UPDATE_AVAILABLE", { v: upd.tag })}
              className="text-(--accent)"
              onClick={installClick}
            >
              <CircleArrowDown size={15} strokeWidth={1.75} />
            </Button>
          </Tip>
        )}

        {/* live status */}
        <button
          onClick={() => app.setSection("events")}
          className="flex h-7 shrink-0 cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-md border border-(--border-hairline) bg-(--bg-surface) px-2.5 text-[12px] text-(--text-secondary) transition-colors hover:border-(--border-strong)"
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              bad ? "bg-(--status-amber)" : "bg-(--status-green)",
            )}
          />
          <span className="max-w-[170px] overflow-hidden font-mono text-[11.5px] whitespace-nowrap opacity-100 transition-[max-width,opacity,margin] max-[1400px]:-mr-1.5 max-[1400px]:max-w-0 max-[1400px]:opacity-0">
            {st ? t("STATUS_SUMMARY", { u: st.infraUp, n: st.infraTotal, mb: st.memMb }) : "…"}
          </span>
          {(issues > 0 || bad) && (
            <span
              className={cn(
                "tnum rounded px-1 font-mono text-[10px]",
                bad ? "bg-(--status-amber)/15 text-(--status-amber)" : "bg-(--bg-hover) text-(--text-secondary)",
              )}
            >
              {Math.max(issues, problems)}
            </span>
          )}
        </button>

        <Tip label={t("INSPECTOR_CTRL_I")}>
          <Button
            variant="ghost"
            size="icon"
            className={cn(app.inspector && "text-(--accent)")}
            onClick={() => app.setInspector(!app.inspector)}
          >
            <PanelRight size={15} strokeWidth={1.75} />
          </Button>
        </Tip>

        {/* window buttons: — □ × (× = to tray). Windows custom frame only:
            macOS has native chrome, web mode has the browser */}
        {st?.platform === "windows" && (
          <>
            <div className="mx-1 h-4 w-px bg-(--border-strong)" />
            <button
              aria-label={t("COLLAPSE")}
              onClick={winCtl("window_minimize")}
              className="flex h-7 w-8 cursor-pointer items-center justify-center rounded-md text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)"
            >
              <Minus size={14} strokeWidth={1.75} />
            </button>
            <button
              aria-label={t("MAXIMIZE_RESTORE")}
              onClick={winCtl("window_toggle_maximize")}
              className="flex h-7 w-8 cursor-pointer items-center justify-center rounded-md text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)"
            >
              <Square size={11} strokeWidth={1.75} />
            </button>
            <button
              aria-label={t("MINIMIZE_TO_TRAY")}
              onClick={winCtl("window_close")}
              className="flex h-7 w-8 cursor-pointer items-center justify-center rounded-md text-(--text-muted) transition-colors hover:bg-(--status-red) hover:text-white"
            >
              <X size={14} strokeWidth={1.75} />
            </button>
          </>
        )}
      </div>
    </header>
  );
}
